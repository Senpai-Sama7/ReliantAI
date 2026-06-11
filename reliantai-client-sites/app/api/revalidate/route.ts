import { revalidatePath } from "next/cache";
import { NextRequest, NextResponse } from "next/server";
import { isValidSlug } from "@/lib/slug";

function timingSafeEqual(a: string, b: string): boolean {
  const bufA = new TextEncoder().encode(a);
  const bufB = new TextEncoder().encode(b);
  if (bufA.length !== bufB.length) return false;
  let result = 0;
  for (let i = 0; i < bufA.length; i++) {
    result |= bufA[i] ^ bufB[i];
  }
  return result === 0;
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

  if (!token || !timingSafeEqual(token, secret)) {
    return NextResponse.json({}, { status: 401 });
  }

  try {
    const body: unknown = await request.json();
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

    return NextResponse.json({ revalidated: true, slug });
  } catch (error) {
    console.error("[revalidate] Failed to parse request body:", error);
    return NextResponse.json(
      { revalidated: false, error: "invalid body" },
      { status: 400 }
    );
  }
}
