import { timingSafeEqual } from "node:crypto";
import { revalidatePath } from "next/cache";
import { NextRequest, NextResponse } from "next/server";
import { isValidSlug } from "@/lib/slug";

function secretsMatch(provided: string, expected: string): boolean {
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

export async function POST(request: NextRequest) {
  const secret = process.env.REVALIDATE_SECRET;
  if (!secret) {
    console.error("[revalidate] REVALIDATE_SECRET is not configured");
    return NextResponse.json(
      { revalidated: false, error: "revalidation not configured" },
      { status: 503 }
    );
  }

  const authHeader = request.headers.get("authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");

  if (!token || !secretsMatch(token, secret)) {
    return NextResponse.json({}, { status: 401 });
  }

  try {
    const raw = await request.text();
    if (raw.length > 4096) {
      return NextResponse.json(
        { revalidated: false, error: "request body too large" },
        { status: 413 }
      );
    }
    const body: unknown = raw ? JSON.parse(raw) : null;
    if (!body || typeof body !== "object" || !("slug" in body)) {
      return NextResponse.json(
        { revalidated: false, error: "slug is required" },
        { status: 400 }
      );
    }

    const slug = (body as { slug?: unknown }).slug;
    if (typeof slug !== "string" || !isValidSlug(slug)) {
      return NextResponse.json(
        { revalidated: false, error: "slug is required and must be a valid slug" },
        { status: 400 }
      );
    }

    revalidatePath(`/${slug}`);

    console.info("[revalidate] success", { slug, path: `/${slug}` });

    return NextResponse.json({ revalidated: true, slug });
  } catch (error) {
    console.error("[revalidate] Failed to parse request body:", error);
    return NextResponse.json(
      { revalidated: false, error: "invalid body" },
      { status: 400 }
    );
  }
}
