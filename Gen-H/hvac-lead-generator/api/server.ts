import express, { Request, Response } from 'express';
import { spawn } from 'child_process';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { Pool } from 'pg';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config({ path: path.resolve(process.cwd(), '../.env') });
dotenv.config();

const app = express();
const leadGeneratorRoot = path.resolve(process.cwd(), '..');
const artifactsDir = path.join(leadGeneratorRoot, 'artifacts');
const bundledPython = path.join(leadGeneratorRoot, '.venv', 'bin', 'python');
const pythonBin = process.env.PYTHON_BIN || (fs.existsSync(bundledPython) ? bundledPython : 'python3');
const pool = new Pool({
  connectionString: process.env.LEAD_DATABASE_URL || process.env.DATABASE_URL,
});

const promotedArtifactNotePrefix = 'Promoted from artifact ';

const getErrorMessage = (error: unknown): string => {
  return error instanceof Error ? error.message : 'Unknown server error';
};

type GeneratorMode = 'profile' | 'dry-run' | 'run';

interface GeneratorRequestBody {
  apiKey?: string;
  entityId?: string;
  target_locations?: string[] | string;
  min_rating?: number;
  min_review_count?: number;
  results_per_location?: number;
  google_sheet_id?: string;
  google_sheet_url?: string;
  preflight_token?: string;
}

interface PromoteArtifactRequestBody {
  artifactFile?: string;
  campaignName?: string;
  google_sheet_id?: string;
}

interface GeneratorRunResult {
  command: string[];
  exitCode: number | null;
  stdout: string;
  stderr: string;
  artifactPath: string;
  artifact: Record<string, unknown> | null;
}

type ReadinessLevel = 'healthy' | 'warning' | 'error';

interface ReadinessCheck {
  key: string;
  label: string;
  status: ReadinessLevel;
  detail: string;
  meta?: Record<string, unknown>;
}

interface ReadinessSnapshot {
  checked_at: string;
  ready_for_profile: boolean;
  ready_for_preview: boolean;
  ready_for_export: boolean;
  ready_for_crm: boolean;
  dependencies: ReadinessCheck[];
}

class HttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const preflightSessions = new Map<string, { configKey: string; expiresAt: number; readiness: ReadinessSnapshot }>();
const preflightTtlMs = 5 * 60 * 1000;

const isPlaceholder = (value?: string): boolean => {
  if (!value) {
    return true;
  }
  const normalized = value.trim().toLowerCase();
  return !normalized || normalized.startsWith('your_') || normalized.endsWith('_here') || normalized.includes('placeholder');
};

const extractGoogleSheetId = (sheetId?: string, sheetUrl?: string): string => {
  if (!isPlaceholder(sheetId)) {
    return sheetId!.trim();
  }

  if (isPlaceholder(sheetUrl)) {
    return '';
  }

  const match = sheetUrl!.match(/\/d\/([a-zA-Z0-9-_]+)/);
  return match?.[1] || '';
};

const normalizeLocations = (value?: string[] | string): string | undefined => {
  if (Array.isArray(value)) {
    return value.map((item) => item.trim()).filter(Boolean).join(';');
  }
  if (typeof value === 'string') {
    return value
      .split(';')
      .map((item) => item.trim())
      .filter(Boolean)
      .join(';');
  }
  return undefined;
};

const buildPreflightConfigKey = (body: GeneratorRequestBody) => {
  const env = buildRuntimeEnv(body);
  return crypto
    .createHash('sha256')
    .update(
      JSON.stringify({
        composio_configured: !isPlaceholder(env.COMPOSIO_API_KEY),
        composio_entity_id: isPlaceholder(env.COMPOSIO_ENTITY_ID) ? '' : env.COMPOSIO_ENTITY_ID,
        target_locations: env.target_locations || '',
        min_rating: env.min_rating || '',
        min_review_count: env.min_review_count || '',
        results_per_location: env.results_per_location || '',
        google_sheet_id: extractGoogleSheetId(env.google_sheet_id, env.google_sheet_url),
      })
    )
    .digest('hex');
};

const issuePreflight = (body: GeneratorRequestBody, readiness: ReadinessSnapshot) => {
  const token = crypto.randomBytes(18).toString('base64url');
  const expiresAt = Date.now() + preflightTtlMs;

  preflightSessions.set(token, {
    configKey: buildPreflightConfigKey(body),
    expiresAt,
    readiness,
  });

  return {
    token,
    expires_at: new Date(expiresAt).toISOString(),
  };
};

const validatePreflight = (mode: GeneratorMode, body: GeneratorRequestBody) => {
  const token = body.preflight_token?.trim();

  if (!token) {
    throw new HttpError(412, 'Run the readiness preflight before executing profile, preview, or export.');
  }

  const session = preflightSessions.get(token);
  if (!session) {
    throw new HttpError(412, 'The readiness preflight token is missing or invalid. Refresh checks and try again.');
  }

  if (session.expiresAt < Date.now()) {
    preflightSessions.delete(token);
    throw new HttpError(412, 'The readiness preflight expired. Refresh checks before executing again.');
  }

  if (session.configKey !== buildPreflightConfigKey(body)) {
    throw new HttpError(412, 'The configuration changed after the last preflight. Refresh checks before executing again.');
  }

  const isAllowed =
    mode === 'profile'
      ? session.readiness.ready_for_profile
      : mode === 'dry-run'
        ? session.readiness.ready_for_preview
        : session.readiness.ready_for_export;

  if (!isAllowed) {
    throw new HttpError(412, `The current readiness report blocks ${mode}. Resolve the failing dependencies and refresh checks.`);
  }
};

const buildRuntimeEnv = (body: GeneratorRequestBody): NodeJS.ProcessEnv => {
  const env: NodeJS.ProcessEnv = { ...process.env };
  const apiKey = body.apiKey?.trim() || process.env.COMPOSIO_API_KEY;
  const entityId = body.entityId?.trim() || process.env.COMPOSIO_ENTITY_ID;

  if (!isPlaceholder(apiKey)) {
    env.COMPOSIO_API_KEY = apiKey;
  }
  if (!isPlaceholder(entityId)) {
    env.COMPOSIO_ENTITY_ID = entityId;
  }

  const locations = normalizeLocations(body.target_locations);
  if (locations) {
    env.target_locations = locations;
  }
  if (typeof body.min_rating === 'number') {
    env.min_rating = String(body.min_rating);
  }
  if (typeof body.min_review_count === 'number') {
    env.min_review_count = String(body.min_review_count);
  }
  if (typeof body.results_per_location === 'number') {
    env.results_per_location = String(body.results_per_location);
  }
  if (body.google_sheet_id?.trim()) {
    env.google_sheet_id = body.google_sheet_id.trim();
  }
  if (body.google_sheet_url?.trim()) {
    env.google_sheet_url = body.google_sheet_url.trim();
  }

  return env;
};

const getDefaultGeneratorConfig = () => ({
  target_locations: (process.env.target_locations || '')
    .split(';')
    .map((item) => item.trim())
    .filter(Boolean),
  min_rating: Number(process.env.min_rating || 3.5),
  min_review_count: Number(process.env.min_review_count || 5),
  results_per_location: Number(process.env.results_per_location || 20),
  google_sheet_id: process.env.google_sheet_id || '',
  google_sheet_url: process.env.google_sheet_url || '',
  has_composio_api_key: !isPlaceholder(process.env.COMPOSIO_API_KEY),
  composio_entity_id: isPlaceholder(process.env.COMPOSIO_ENTITY_ID) ? '' : process.env.COMPOSIO_ENTITY_ID || '',
});

const readArtifact = (artifactPath: string): Record<string, unknown> | null => {
  if (!fs.existsSync(artifactPath)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(artifactPath, 'utf-8')) as Record<string, unknown>;
};

const initDatabase = async () => {
  await pool.query(
    `ALTER TABLE lead_campaigns
     ADD COLUMN IF NOT EXISTS source_artifact_file VARCHAR(255)`
  );

  await pool.query(
    `CREATE UNIQUE INDEX IF NOT EXISTS idx_campaigns_source_artifact_file
     ON lead_campaigns(source_artifact_file)
     WHERE source_artifact_file IS NOT NULL`
  );
};

const findExistingArtifactCampaign = async (artifactFile: string) => {
  const directMatch = await pool.query(
    `SELECT *
     FROM lead_campaigns
     WHERE source_artifact_file = $1
     LIMIT 1`,
    [artifactFile]
  );

  if (directMatch.rows[0]) {
    return directMatch.rows[0];
  }

  const legacyMatch = await pool.query(
    `SELECT lc.*
     FROM lead_campaigns lc
     INNER JOIN leads l ON l.campaign_id = lc.id
     WHERE l.notes = $1
     ORDER BY lc.created_at DESC
     LIMIT 1`,
    [`${promotedArtifactNotePrefix}${artifactFile}`]
  );

  return legacyMatch.rows[0] || null;
};

const resolveArtifactPath = (fileName: string): string => {
  return path.join(artifactsDir, path.basename(fileName));
};

const listArtifacts = async (): Promise<Record<string, unknown>[]> => {
  if (!fs.existsSync(artifactsDir)) {
    return [];
  }

  const files = fs
    .readdirSync(artifactsDir)
    .filter((file) => file.endsWith('.json'))
    .sort()
    .reverse();

  return Promise.all(
    files.map(async (file) => {
      const absolutePath = path.join(artifactsDir, file);
      const payload = readArtifact(absolutePath) || {};
      const existingCampaign = await findExistingArtifactCampaign(file);
      return {
        file,
        path: absolutePath,
        mode: payload.mode || 'unknown',
        generated_at: payload.generated_at || null,
        total_leads_found: payload.total_leads_found ?? null,
        sheet_name: payload.sheet_name ?? null,
        spreadsheet_url: payload.spreadsheet_url ?? null,
        dry_run: payload.dry_run ?? false,
        sample_leads: Array.isArray(payload.sample_leads) ? payload.sample_leads : [],
        is_promoted: Boolean(existingCampaign),
        promoted_campaign: existingCampaign
          ? {
              id: existingCampaign.id,
              name: existingCampaign.name,
              status: existingCampaign.status,
            }
          : null,
      };
    })
  );
};

const evaluateReadiness = async (body: GeneratorRequestBody = {}): Promise<ReadinessSnapshot> => {
  const env = buildRuntimeEnv(body);
  const dependencies: ReadinessCheck[] = [];

  dependencies.push({
    key: 'api',
    label: 'API Status',
    status: 'healthy',
    detail: 'Lead API is running and accepting operator requests.',
    meta: {
      uptime_seconds: Math.round(process.uptime()),
      port: Number(process.env.LEAD_API_PORT || process.env.PORT || 5001),
    },
  });

  const pythonIsPath = path.isAbsolute(pythonBin) || pythonBin.includes(path.sep);
  const pythonAvailable = pythonIsPath ? fs.existsSync(pythonBin) : true;
  dependencies.push({
    key: 'python',
    label: 'Python Runtime',
    status: pythonAvailable ? 'healthy' : 'error',
    detail: pythonAvailable
      ? `Generator runtime available via ${pythonBin}.`
      : `Generator runtime not found at ${pythonBin}.`,
    meta: { command: pythonBin },
  });

  const composioKey = env.COMPOSIO_API_KEY;
  const composioEntityId = env.COMPOSIO_ENTITY_ID;
  const composioReady = !isPlaceholder(composioKey) && !isPlaceholder(composioEntityId);
  dependencies.push({
    key: 'composio',
    label: 'Composio Session',
    status: composioReady ? 'healthy' : 'error',
    detail: composioReady
      ? `Composio credentials are configured for entity ${composioEntityId}.`
      : 'Composio API key or entity ID is missing. Profile, preview, and export are blocked until both are configured.',
    meta: {
      has_api_key: !isPlaceholder(composioKey),
      entity_id: !isPlaceholder(composioEntityId) ? composioEntityId : null,
    },
  });

  try {
    const postgresResult = await pool.query('SELECT current_database() AS database_name');
    dependencies.push({
      key: 'postgres',
      label: 'Postgres CRM',
      status: 'healthy',
      detail: `CRM database online (${postgresResult.rows[0]?.database_name || 'connected'}).`,
    });
  } catch (error) {
    dependencies.push({
      key: 'postgres',
      label: 'Postgres CRM',
      status: 'error',
      detail: `Database check failed: ${getErrorMessage(error)}`,
    });
  }

  try {
    fs.mkdirSync(artifactsDir, { recursive: true });
    fs.accessSync(artifactsDir, fs.constants.R_OK | fs.constants.W_OK);
    const artifactCount = fs.readdirSync(artifactsDir).filter((file) => file.endsWith('.json')).length;
    dependencies.push({
      key: 'artifacts',
      label: 'Artifact Storage',
      status: 'healthy',
      detail: `Artifact directory is writable with ${artifactCount} JSON files available.`,
      meta: { path: artifactsDir, artifact_count: artifactCount },
    });
  } catch (error) {
    dependencies.push({
      key: 'artifacts',
      label: 'Artifact Storage',
      status: 'error',
      detail: `Artifact storage check failed: ${getErrorMessage(error)}`,
      meta: { path: artifactsDir },
    });
  }

  const resolvedSheetId = extractGoogleSheetId(env.google_sheet_id, env.google_sheet_url);
  const googleSheetsReady = !isPlaceholder(resolvedSheetId);
  dependencies.push({
    key: 'google-sheets',
    label: 'Google Sheets Target',
    status: googleSheetsReady ? 'healthy' : 'warning',
    detail: googleSheetsReady
      ? `Export target is configured for spreadsheet ${resolvedSheetId}.`
      : 'No Google Sheet target is configured. Profile and preview still work, but live export is blocked.',
    meta: { sheet_id: googleSheetsReady ? resolvedSheetId : null },
  });

  const statusByKey = Object.fromEntries(dependencies.map((item) => [item.key, item.status]));
  const generatorReady =
    statusByKey.api === 'healthy' &&
    statusByKey.python === 'healthy' &&
    statusByKey.composio === 'healthy' &&
    statusByKey.artifacts === 'healthy';

  return {
    checked_at: new Date().toISOString(),
    ready_for_profile: generatorReady,
    ready_for_preview: generatorReady,
    ready_for_export: generatorReady && statusByKey['google-sheets'] === 'healthy',
    ready_for_crm: statusByKey.postgres === 'healthy',
    dependencies,
  };
};

const runGenerator = (mode: GeneratorMode, body: GeneratorRequestBody): Promise<GeneratorRunResult> => {
  fs.mkdirSync(artifactsDir, { recursive: true });

  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const artifactPath = path.join(artifactsDir, `${mode}-${stamp}.json`);
  const args = ['lead_generator.py'];

  if (mode === 'profile') {
    args.push('--profile-locations');
  } else if (mode === 'dry-run') {
    args.push('--dry-run');
  }

  args.push('--output-json', artifactPath);

  const env = buildRuntimeEnv(body);

  return new Promise((resolve, reject) => {
    const child = spawn(pythonBin, args, {
      cwd: leadGeneratorRoot,
      env,
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    child.on('error', (error) => {
      reject(error);
    });

    child.on('close', (exitCode) => {
      resolve({
        command: [pythonBin, ...args],
        exitCode,
        stdout,
        stderr,
        artifactPath,
        artifact: readArtifact(artifactPath),
      });
    });
  });
};

app.use(cors());
app.use(express.json());

app.get('/health', (_req: Request, res: Response) => {
  res.json({ success: true, service: 'hvac-lead-gen-api' });
});

app.get('/api/system/config', async (_req: Request, res: Response) => {
  try {
    res.json({
      success: true,
      data: {
        defaults: getDefaultGeneratorConfig(),
        artifacts: await listArtifacts(),
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/system/readiness', async (req: Request, res: Response) => {
  try {
    const body = (req.body || {}) as GeneratorRequestBody;
    const readiness = await evaluateReadiness(body);
    res.json({
      success: true,
      data: {
        ...readiness,
        preflight: issuePreflight(body, readiness),
      },
    });
  } catch (error) {
    const status = error instanceof HttpError ? error.status : 500;
    res.status(status).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/system/history', async (_req: Request, res: Response) => {
  try {
    res.json({ success: true, data: await listArtifacts() });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/system/history/:file', (req: Request, res: Response) => {
  const file = path.basename(req.params.file);
  const artifactPath = resolveArtifactPath(file);
  const artifact = readArtifact(artifactPath);

  if (!artifact) {
    res.status(404).json({ success: false, error: 'Artifact not found.' });
    return;
  }

  res.json({ success: true, data: { file, path: artifactPath, artifact } });
});

app.get('/api/system/history/:file/download', (req: Request, res: Response) => {
  const file = path.basename(req.params.file);
  const artifactPath = resolveArtifactPath(file);

  if (!fs.existsSync(artifactPath)) {
    res.status(404).json({ success: false, error: 'Artifact not found.' });
    return;
  }

  res.download(artifactPath, file);
});

app.post('/api/system/profile', async (req: Request, res: Response) => {
  try {
    const body = (req.body || {}) as GeneratorRequestBody;
    validatePreflight('profile', body);
    const result = await runGenerator('profile', body);
    res.status(result.exitCode === 0 ? 200 : 500).json({ success: result.exitCode === 0, data: result });
  } catch (error) {
    const status = error instanceof HttpError ? error.status : 500;
    res.status(status).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/system/dry-run', async (req: Request, res: Response) => {
  try {
    const body = (req.body || {}) as GeneratorRequestBody;
    validatePreflight('dry-run', body);
    const result = await runGenerator('dry-run', body);
    res.status(result.exitCode === 0 ? 200 : 500).json({ success: result.exitCode === 0, data: result });
  } catch (error) {
    const status = error instanceof HttpError ? error.status : 500;
    res.status(status).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/system/run', async (req: Request, res: Response) => {
  try {
    const body = (req.body || {}) as GeneratorRequestBody;
    validatePreflight('run', body);
    const result = await runGenerator('run', body);
    res.status(result.exitCode === 0 ? 200 : 500).json({ success: result.exitCode === 0, data: result });
  } catch (error) {
    const status = error instanceof HttpError ? error.status : 500;
    res.status(status).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/system/promote', async (req: Request, res: Response) => {
  const body = (req.body || {}) as PromoteArtifactRequestBody;

  try {
    if (!body.artifactFile) {
      res.status(400).json({ success: false, error: 'artifactFile is required.' });
      return;
    }

    const file = path.basename(body.artifactFile);
    const artifactPath = resolveArtifactPath(file);
    const artifact = readArtifact(artifactPath);

    if (!artifact) {
      res.status(404).json({ success: false, error: 'Artifact not found.' });
      return;
    }

    const leads = Array.isArray(artifact.leads)
      ? (artifact.leads as Record<string, unknown>[])
      : Array.isArray(artifact.sample_leads)
        ? (artifact.sample_leads as Record<string, unknown>[])
        : [];

    if (leads.length === 0) {
      res.status(400).json({ success: false, error: 'This artifact does not contain any leads to promote.' });
      return;
    }

    const existingCampaign = await findExistingArtifactCampaign(file);
    if (existingCampaign) {
      res.status(409).json({
        success: false,
        error: `This artifact has already been promoted into campaign “${existingCampaign.name}”.`,
        data: {
          campaign: existingCampaign,
          artifactFile: file,
        },
      });
      return;
    }

    const locations = Array.isArray(artifact.locations_searched)
      ? (artifact.locations_searched as string[])
      : Array.isArray((artifact.config as Record<string, unknown> | undefined)?.target_locations)
        ? (((artifact.config as Record<string, unknown>).target_locations as string[]) || [])
        : [];
    const criteria = (artifact.filter_criteria as Record<string, unknown> | undefined) || {};
    const config = (artifact.config as Record<string, unknown> | undefined) || {};
    const minRating = Number(criteria.min_rating ?? config.min_rating ?? 0);
    const minReviewCount = Number(criteria.min_reviews ?? config.min_review_count ?? 0);
    const resultsPerLocation = Number(config.results_per_location ?? 20);
    const defaultNameParts = [
      artifact.mode === 'dry-run' ? 'Preview' : 'Artifact',
      Array.isArray(locations) && locations.length > 0 ? locations[0] : null,
      artifact.generated_at ? String(artifact.generated_at) : null,
    ].filter(Boolean);
    const campaignName = body.campaignName?.trim() || defaultNameParts.join(' · ');
    const googleSheetId = body.google_sheet_id?.trim() || String(artifact.spreadsheet_id || '') || null;

    const client = await pool.connect();

    try {
      await client.query('BEGIN');

      const campaignResult = await client.query(
        `INSERT INTO lead_campaigns
         (name, target_locations, min_rating, min_review_count, results_per_location, google_sheet_id, status, started_at, source_artifact_file)
         VALUES ($1, $2, $3, $4, $5, $6, 'running', CURRENT_TIMESTAMP, $7)
         RETURNING *`,
        [campaignName, locations, minRating, minReviewCount, resultsPerLocation, googleSheetId, file]
      );

      const campaign = campaignResult.rows[0];

      for (const lead of leads) {
        await client.query(
          `INSERT INTO leads
           (campaign_id, company_name, phone, email, address, rating, review_count, years_in_business,
            services_offered, specialties, service_area, unique_selling_points, google_maps_url,
            research_sources, location_searched, outreach_status, notes)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, 'new', $16)`,
          [
            campaign.id,
            String(lead.name || lead.company_name || 'Unknown Company'),
            lead.phone ? String(lead.phone) : null,
            lead.email ? String(lead.email) : null,
            lead.address ? String(lead.address) : null,
            lead.rating != null ? Number(lead.rating) : null,
            lead.review_count != null ? Number(lead.review_count) : null,
            lead.years_in_business ? String(lead.years_in_business) : null,
            lead.services_offered ? String(lead.services_offered) : null,
            lead.specialties ? String(lead.specialties) : null,
            lead.service_area ? String(lead.service_area) : null,
            lead.unique_selling_points ? String(lead.unique_selling_points) : null,
            lead.google_maps_url ? String(lead.google_maps_url) : null,
            lead.research_sources ? String(lead.research_sources) : null,
            lead.location ? String(lead.location) : null,
            `${promotedArtifactNotePrefix}${file}`,
          ]
        );
      }

      await client.query('COMMIT');
      res.status(201).json({
        success: true,
        data: {
          campaign,
          insertedLeads: leads.length,
          artifactFile: file,
        },
      });
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/campaigns', async (req: Request, res: Response) => {
  try {
    const {
      name,
      target_locations,
      min_rating,
      min_review_count,
      results_per_location,
      google_sheet_id,
    } = req.body;

    const result = await pool.query(
      `INSERT INTO lead_campaigns
       (name, target_locations, min_rating, min_review_count, results_per_location, google_sheet_id)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING *`,
      [name, target_locations, min_rating, min_review_count, results_per_location, google_sheet_id]
    );

    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/campaigns', async (req: Request, res: Response) => {
  try {
    const { status } = req.query;
    let query = 'SELECT * FROM lead_campaigns';
    const params: unknown[] = [];

    if (status) {
      query += ' WHERE status = $1';
      params.push(status);
    }

    query += ' ORDER BY created_at DESC';
    const result = await pool.query(query, params);

    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/campaigns/:id/start', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `UPDATE lead_campaigns
       SET status = 'running', started_at = CURRENT_TIMESTAMP
       WHERE id = $1
       RETURNING *`,
      [id]
    );

    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/campaigns/:campaign_id/leads', async (req: Request, res: Response) => {
  try {
    const { campaign_id } = req.params;
    const { outreach_status } = req.query;

    let query = 'SELECT * FROM leads WHERE campaign_id = $1';
    const params: unknown[] = [campaign_id];

    if (outreach_status) {
      query += ' AND outreach_status = $2';
      params.push(outreach_status);
    }

    query += ' ORDER BY rating DESC NULLS LAST, review_count DESC NULLS LAST';
    const result = await pool.query(query, params);

    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.patch('/api/leads/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { outreach_status, notes } = req.body;

    const result = await pool.query(
      `UPDATE leads
       SET outreach_status = $1, notes = $2, updated_at = CURRENT_TIMESTAMP
       WHERE id = $3
       RETURNING *`,
      [outreach_status, notes, id]
    );

    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/campaigns/:id/stats', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `SELECT
        COUNT(*) AS total_leads,
        COUNT(*) FILTER (WHERE outreach_status = 'contacted') AS contacted,
        COUNT(*) FILTER (WHERE outreach_status = 'interested') AS interested,
        COUNT(*) FILTER (WHERE email IS NOT NULL AND email != 'Not found') AS has_email,
        AVG(rating) AS avg_rating,
        AVG(review_count) AS avg_reviews
       FROM leads
       WHERE campaign_id = $1`,
      [id]
    );

    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

const port = Number(process.env.LEAD_API_PORT || process.env.PORT || 5001);
initDatabase()
  .then(() => {
    app.listen(port, () => {
      console.log(`Lead Generator API running on port ${port}`);
    });
  })
  .catch((error) => {
    console.error('Failed to initialize lead database schema:', error);
    process.exit(1);
  });
