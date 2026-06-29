import { readFileSync } from "node:fs";
import { join } from "node:path";
import { isValidSlug } from "../../../lib/slug.js";

const sites = JSON.parse(
  readFileSync(join(process.cwd(), "data", "sites.json"), "utf8")
);

export default function handler(req, res) {
  const slug = Array.isArray(req.query.slug)
    ? req.query.slug[0]
    : req.query.slug;

  if (!slug || !isValidSlug(slug)) {
    res.status(400).json({ detail: "Invalid slug" });
    return;
  }

  const site = sites[slug];
  if (!site) {
    res.status(404).json({ detail: "Site not found" });
    return;
  }

  res.status(200).json(site);
}
