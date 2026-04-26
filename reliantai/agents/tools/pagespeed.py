import os
import httpx
from crewai.tools import BaseTool


class PageSpeedTool(BaseTool):
    name: str = "pagespeed_analyzer"
    description: str = (
        "Analyze a website URL with Google PageSpeed Insights. "
        "Returns performance score, Core Web Vitals (LCP, FID, CLS), and SSL status."
    )

    def _run(self, url: str) -> str:
        if not url:
            return str({"score": 0, "error": "no_url"})

        api_key = os.environ.get("GOOGLE_PAGESPEED_API_KEY", "")
        params = {
            "url": url,
            "strategy": "mobile",
            "category": "performance",
        }
        if api_key:
            params["key"] = api_key

        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(
                    "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                    params=params,
                )
            if resp.status_code != 200:
                return str({"score": 0, "error": f"HTTP {resp.status_code}"})

            data = resp.json()
            lh = data.get("lighthouseResult", {})
            audits = lh.get("audits", {})

            score = int(lh.get("categories", {}).get("performance", {}).get("score", 0) * 100)
            lcp = audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000
            fid = audits.get("max-potential-fid", {}).get("numericValue", 0)
            cls = audits.get("cumulative-layout-shift", {}).get("numericValue", 0)
            has_ssl = url.startswith("https://")

            return str({
                "score": score,
                "lcp": round(lcp, 2),
                "fid": round(fid, 0),
                "cls": round(cls, 3),
                "has_ssl": has_ssl,
            })
        except httpx.TimeoutException:
            return str({"score": 0, "error": "timeout"})
        except httpx.HTTPStatusError as e:
            return str({"score": 0, "error": f"http_error_{e.response.status_code}"})
        except (httpx.RequestError, ValueError, KeyError) as e:
            return str({"score": 0, "error": str(e)[:100]})
