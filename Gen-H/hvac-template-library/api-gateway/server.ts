import express, { Request, Response } from 'express';
import cors from 'cors';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(process.cwd(), '../.env'), override: true });
dotenv.config();

const app = express();
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const getErrorMessage = (error: unknown): string => {
  return error instanceof Error ? error.message : 'Unknown server error';
};

app.use(cors());
app.use(express.json());

app.get('/health', (_req: Request, res: Response) => {
  res.json({ success: true, service: 'hvac-template-api' });
});

app.get('/api/templates', async (req: Request, res: Response) => {
  try {
    const { framework, status } = req.query;
    let query = 'SELECT * FROM templates WHERE 1=1';
    const params: unknown[] = [];

    if (framework) {
      query += ' AND framework = $' + (params.length + 1);
      params.push(framework);
    }
    if (status) {
      query += ' AND status = $' + (params.length + 1);
      params.push(status);
    }

    query += ' ORDER BY created_at DESC';
    const result = await pool.query(query, params);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/templates/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM templates WHERE id = $1 OR slug = $1', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Template not found' });
    }

    return res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    return res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/templates', async (req: Request, res: Response) => {
  try {
    const {
      name,
      slug,
      description,
      framework,
      primary_color,
      secondary_color,
      accent_color,
      typography_headline,
      typography_body,
      has_3d_viewer,
      has_calculator,
      has_before_after,
      has_testimonials,
      frontend_repo_url,
      backend_repo_url,
      created_by,
    } = req.body;

    const result = await pool.query(
      `INSERT INTO templates
       (name, slug, description, framework, primary_color, secondary_color,
        accent_color, typography_headline, typography_body, has_3d_viewer,
        has_calculator, has_before_after, has_testimonials, frontend_repo_url,
        backend_repo_url, created_by, status)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, 'active')
       RETURNING *`,
      [
        name,
        slug,
        description,
        framework,
        primary_color,
        secondary_color,
        accent_color,
        typography_headline,
        typography_body,
        has_3d_viewer,
        has_calculator,
        has_before_after,
        has_testimonials,
        frontend_repo_url,
        backend_repo_url,
        created_by,
      ]
    );

    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/companies', async (_req: Request, res: Response) => {
  try {
    const result = await pool.query('SELECT * FROM companies ORDER BY created_at DESC');
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/companies', async (req: Request, res: Response) => {
  try {
    const { name, slug, email, phone, owner_name, owner_email, business_type } = req.body;

    const result = await pool.query(
      `INSERT INTO companies (name, slug, email, phone, owner_name, owner_email, business_type)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING *`,
      [name, slug, email, phone, owner_name, owner_email, business_type]
    );

    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/deployments', async (req: Request, res: Response) => {
  try {
    const { company_id, template_id, status } = req.query;
    let query = 'SELECT * FROM deployments WHERE 1=1';
    const params: unknown[] = [];

    if (company_id) {
      query += ' AND company_id = $' + (params.length + 1);
      params.push(company_id);
    }
    if (template_id) {
      query += ' AND template_id = $' + (params.length + 1);
      params.push(template_id);
    }
    if (status) {
      query += ' AND status = $' + (params.length + 1);
      params.push(status);
    }

    query += ' ORDER BY created_at DESC';
    const result = await pool.query(query, params);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/deployments', async (req: Request, res: Response) => {
  try {
    const { template_id, company_id, domain, customizations, deployed_by } = req.body;

    const result = await pool.query(
      `INSERT INTO deployments
       (template_id, company_id, domain, customizations, deployed_by, status)
       VALUES ($1, $2, $3, $4, $5, 'pending')
       RETURNING *`,
      [template_id, company_id, domain, JSON.stringify(customizations ?? {}), deployed_by]
    );

    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.patch('/api/deployments/:id/customize', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { customizations, custom_content } = req.body;

    const result = await pool.query(
      `UPDATE deployments
       SET customizations = $1, custom_content = $2, updated_at = CURRENT_TIMESTAMP
       WHERE id = $3
       RETURNING *`,
      [JSON.stringify(customizations ?? {}), JSON.stringify(custom_content ?? {}), id]
    );

    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/deployments/:id/deploy', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `UPDATE deployments
       SET status = 'deploying', deployment_date = CURRENT_TIMESTAMP
       WHERE id = $1
       RETURNING *`,
      [id]
    );

    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.post('/api/analytics/:deployment_id', async (req: Request, res: Response) => {
  try {
    const { deployment_id } = req.params;
    const { event_type, event_data } = req.body;

    await pool.query(
      `INSERT INTO analytics_events (deployment_id, event_type, event_data)
       VALUES ($1, $2, $3)`,
      [deployment_id, event_type, JSON.stringify(event_data ?? {})]
    );

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

app.get('/api/deployments/:id/analytics', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `SELECT
        event_type,
        COUNT(*) AS count,
        COUNT(DISTINCT user_ip) AS unique_users
       FROM analytics_events
       WHERE deployment_id = $1
       GROUP BY event_type`,
      [id]
    );

    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

// Mockup endpoint for ReliantAI.org dynamic site generation
app.get('/preview/:slug', async (req: Request, res: Response) => {
  try {
    const { slug } = req.params;
    // Generate dynamic mockup configuration
    res.json({ 
      success: true, 
      preview_url: `https://reliantai.org/preview/${slug}`,
      mockup_data: {
        theme: "modern",
        primary_color: "#1e3a8a",
        business_name: slug.replace(/-/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
        features: ["AEO Optimized", "GEO Mapped", "Fast SSR"]
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: getErrorMessage(error) });
  }
});

const port = Number(process.env.API_PORT || process.env.PORT || 5000);
app.listen(port, () => {
  console.log(`API Gateway running on port ${port}`);
});
