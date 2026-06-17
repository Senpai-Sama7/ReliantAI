import { describe, expect, it } from "vitest";
import { serializeJsonLd } from "@/lib/serialize-json-ld";
import { isValidSlug, MAX_SLUG_LENGTH } from "@/lib/slug";
import { sanitizeHttpUrl } from "@/lib/safe-url";
import { parseSiteContent } from "@/lib/validate-site-content";

describe("isValidSlug", () => {
  it("accepts lowercase hyphenated slugs", () => {
    expect(isValidSlug("apex-hvac-houston-ab12")).toBe(true);
  });

  it("rejects uppercase, slashes, and traversal patterns", () => {
    expect(isValidSlug("../admin")).toBe(false);
    expect(isValidSlug("Bad-Slug")).toBe(false);
    expect(isValidSlug("")).toBe(false);
  });

  it("enforces max length", () => {
    const longSlug = "a".repeat(MAX_SLUG_LENGTH + 1);
    expect(isValidSlug(longSlug)).toBe(false);
  });
});

describe("serializeJsonLd", () => {
  it("escapes script breakouts", () => {
    const payload = { name: "</script><script>alert(1)</script>" };
    const serialized = serializeJsonLd(payload);
    expect(serialized).not.toContain("</script>");
    expect(JSON.parse(serialized)).toEqual(payload);
  });

  it("returns an object string for undefined input", () => {
    expect(serializeJsonLd(undefined)).toBe("{}");
  });
});

describe("sanitizeHttpUrl", () => {
  it("accepts https URLs and normalizes bare domains", () => {
    expect(sanitizeHttpUrl("https://example.com/path")).toBe(
      "https://example.com/path",
    );
    expect(sanitizeHttpUrl("example.com")).toBe("https://example.com/");
  });

  it("rejects javascript and data URIs", () => {
    expect(sanitizeHttpUrl("javascript:alert(1)")).toBeNull();
    expect(sanitizeHttpUrl("data:text/html,hi")).toBeNull();
  });
});

describe("parseSiteContent", () => {
  const validPayload = {
    slug: "apex-hvac-houston-ab12",
    business: { business_name: "Apex HVAC" },
    hero: { headline: "Apex HVAC" },
    site_config: { template_id: "hvac-reliable-blue" },
    services: [],
    about: { body: "About us" },
    reviews: { rating: 4.8 },
    faq: [],
  };

  it("accepts a minimal valid payload", () => {
    expect(parseSiteContent(validPayload)?.slug).toBe("apex-hvac-houston-ab12");
  });

  it("rejects unknown templates and invalid slugs", () => {
    expect(
      parseSiteContent({
        ...validPayload,
        site_config: { template_id: "unknown-template" },
      }),
    ).toBeNull();
    expect(parseSiteContent({ ...validPayload, slug: "bad slug" })).toBeNull();
  });

  it("strips unsafe business website URLs", () => {
    const parsed = parseSiteContent({
      ...validPayload,
      business: {
        business_name: "Apex HVAC",
        website_url: "javascript:alert(1)",
      },
    });
    expect(parsed?.business.website_url).toBeUndefined();
  });
});
