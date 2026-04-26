import { revalidatePath, revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

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
  const authHeader = request.headers.get("authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");
  const secret = process.env.REVALIDATE_SECRET || "";

  if (!token || !timingSafeEqual(token, secret)) {
    return NextResponse.json({}, { status: 401 });
  }

  try {
    const body = await request.json();
    const { slug } = body as { slug?: string };

    if (!slug || typeof slug !== "string") {
      return NextResponse.json(
        { revalidated: false, error: "slug is required" },
        { status: 400 }
      );
    }

    revalidatePath(`/${slug}`);

    return NextResponse.json({ revalidated: true, slug });
  } catch {
    return NextResponse.json(
      { revalidated: false, error: "invalid body" },
      { status: 400 }
    );
  }
}
