function readFileAs<T>(file: File, method: 'readAsText' | 'readAsDataURL' | 'readAsArrayBuffer'): Promise<T> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as T);
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`));
    reader[method](file);
  });
}

const readFileAsText = (file: File) => readFileAs<string>(file, 'readAsText');
const readFileAsArrayBuffer = (file: File) => readFileAs<ArrayBuffer>(file, 'readAsArrayBuffer');

// --- Format-specific extractors (all lazy-loaded) ---

async function extractPdfText(file: File): Promise<string> {
  const pdfjsLib = await import('pdfjs-dist');
  pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url,
  ).toString();
  const buffer = await readFileAsArrayBuffer(file);
  const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
  const pages: string[] = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    pages.push(content.items.map((item: any) => item.str).join(' '));
  }
  const text = pages.join('\n\n').trim();
  if (!text) throw new Error(`PDF "${file.name}" has no extractable text layer. It may be a scanned image — try uploading as an image for OCR.`);
  return text;
}

async function extractImageText(file: File): Promise<string> {
  const { createWorker } = await import('tesseract.js');
  const worker = await createWorker('eng');
  try {
    const buffer = await readFileAsArrayBuffer(file);
    const { data } = await worker.recognize(new Uint8Array(buffer));
    const text = data.text.trim();
    if (!text) throw new Error(`OCR found no readable text in image "${file.name}". The image may be too low-resolution or contain no text.`);
    return text;
  } finally {
    await worker.terminate();
  }
}

async function extractDocxText(file: File): Promise<string> {
  const mammoth = await import('mammoth');
  const buffer = await readFileAsArrayBuffer(file);
  const result = await mammoth.default.extractRawText({ arrayBuffer: buffer });
  const text = result.value.trim();
  if (!text) throw new Error(`Word document "${file.name}" contains no extractable text.`);
  return text;
}

async function extractXlsxText(file: File): Promise<string> {
  const XLSX = await import('xlsx');
  const buffer = await readFileAsArrayBuffer(file);
  const workbook = XLSX.read(buffer, { type: 'array' });
  const sheets: string[] = [];
  for (const name of workbook.SheetNames) {
    const csv = XLSX.utils.sheet_to_csv(workbook.Sheets[name]);
    if (csv.trim()) sheets.push(`--- Sheet: ${name} ---\n${csv}`);
  }
  if (!sheets.length) throw new Error(`Spreadsheet "${file.name}" contains no data in any sheet.`);
  return sheets.join('\n\n');
}

function extractEmlText(raw: string, filename: string): string {
  // Split headers from body at first blank line
  const split = raw.indexOf('\n\n');
  if (split === -1) throw new Error(`EML file "${filename}" has no message body.`);
  const headers = raw.slice(0, split);
  let body = raw.slice(split + 2);

  // Extract key headers
  const getHeader = (name: string) => headers.match(new RegExp(`^${name}:\\s*(.+)$`, 'mi'))?.[1]?.trim() || '';
  const meta = ['From', 'To', 'Subject', 'Date'].map(h => `${h}: ${getHeader(h)}`).filter(l => !l.endsWith(': ')).join('\n');

  // If multipart, grab the first text/plain part
  const boundary = headers.match(/boundary="?([^"\s;]+)"?/i)?.[1];
  if (boundary) {
    const parts = body.split(`--${boundary}`);
    const textPart = parts.find(p => /content-type:\s*text\/plain/i.test(p));
    if (textPart) {
      const partBody = textPart.indexOf('\n\n');
      body = partBody !== -1 ? textPart.slice(partBody + 2) : textPart;
    }
  }

  const text = body.replace(/--[\w-]+--?\s*$/g, '').trim();
  if (!text && !meta) throw new Error(`EML file "${filename}" contains no readable content.`);
  return meta ? `${meta}\n\n${text}` : text;
}

// --- Main dispatcher ---

export async function extractTextFromFile(file: File): Promise<string> {
  const type = file.type;
  const name = file.name.toLowerCase();

  try {
    // Text / CSV / JSON / Markdown
    if (type.startsWith('text/') || /\.(txt|csv|json|md)$/.test(name))
      return await readFileAsText(file);

    // PDF
    if (type === 'application/pdf' || name.endsWith('.pdf'))
      return await extractPdfText(file);

    // Images (OCR)
    if (type.startsWith('image/') || /\.(png|jpe?g|tiff?)$/.test(name))
      return await extractImageText(file);

    // XLSX / XLS
    if (name.endsWith('.xlsx') || name.endsWith('.xls'))
      return await extractXlsxText(file);

    // DOCX
    if (name.endsWith('.docx'))
      return await extractDocxText(file);

    // EML
    if (name.endsWith('.eml') || type === 'message/rfc822') {
      const raw = await readFileAsText(file);
      return extractEmlText(raw, file.name);
    }
  } catch (err) {
    // Re-throw with format context if not already specific
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes(file.name)) throw err;
    throw new Error(`Failed to extract text from ${file.name}: ${msg}`);
  }

  throw new Error(`Unsupported file format: ${file.name} (${type || 'unknown type'})`);
}

export function isValidDocumentFile(file: File): boolean {
  const validTypes = [
    'application/pdf', 'text/plain', 'text/csv',
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/tiff',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'message/rfc822',
  ];
  const validExts = ['.pdf', '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.tif', '.tiff', '.doc', '.docx', '.xls', '.xlsx', '.eml'];
  return validTypes.includes(file.type) || validExts.some(e => file.name.toLowerCase().endsWith(e));
}
