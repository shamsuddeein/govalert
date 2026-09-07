import OpenAI from "openai";

export interface DetectionAnalysis {
  isRecruitment: boolean;
  title: string;
  positions: string;
  deadline: string;
  requirements: string;
  confidenceScore: number;
  aiClassification: "REAL" | "FAKE" | "UNCERTAIN";
  aiConfidence: number;
  redFlags: string[];
  confidenceFactors: Array<{ label: string; passed: boolean }>;
}

export async function analyzePortalText(
  pageText: string,
  portalUrl: string,
  officialDomain?: string
): Promise<DetectionAnalysis> {
  const apiKey = process.env.OPENAI_API_KEY;

  if (apiKey) {
    try {
      const openai = new OpenAI({ apiKey });
      const prompt = `You are a Nigerian Public Sector Recruitment Fraud Analyst.
Analyze the following webpage text from ${portalUrl} (Official Agency Domain: ${officialDomain || "N/A"}).
Determine if this page contains an active government recruitment announcement.

Detect red flags:
1. Demanding money/registration fees/processing charges (Nigerian civil service recruitment is 100% free by law).
2. Contact emails using generic providers (@gmail.com, @yahoo.com, @hotmail.com) instead of official .gov.ng domains.
3. WhatsApp or personal phone numbers as the primary submission channel.
4. Non-governmental domain hosts (.blogspot, .wix, .wordpress, .site, .online) pretending to be official agencies.

Text to inspect:
${pageText.slice(0, 6000)}

Respond strictly in JSON format matching this schema:
{
  "isRecruitment": boolean,
  "title": string,
  "positions": string,
  "deadline": string (YYYY-MM-DD or "Ongoing"),
  "requirements": string,
  "confidenceScore": number (0 to 100),
  "aiClassification": "REAL" | "FAKE" | "UNCERTAIN",
  "aiConfidence": number (0 to 100),
  "redFlags": string[],
  "factors": [
    {"label": "Official Domain Match", "passed": boolean},
    {"label": "Zero Application Fees", "passed": boolean},
    {"label": "Official Application Portal Link", "passed": boolean},
    {"label": "No Suspicious Free Email Contacts", "passed": boolean}
  ]
}`;

      const completion = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: prompt }],
        response_format: { type: "json_object" },
        temperature: 0.1,
      });

      const parsed = JSON.parse(completion.choices[0].message.content || "{}");
      return {
        isRecruitment: Boolean(parsed.isRecruitment),
        title: String(parsed.title || "Government Recruitment Notice"),
        positions: String(parsed.positions || "Various Positions"),
        deadline: String(parsed.deadline || "TBA"),
        requirements: String(parsed.requirements || "Details available on portal"),
        confidenceScore: Number(parsed.confidenceScore) || 50,
        aiClassification: parsed.aiClassification || "UNCERTAIN",
        aiConfidence: Number(parsed.aiConfidence) || 50,
        redFlags: Array.isArray(parsed.redFlags) ? parsed.redFlags : [],
        confidenceFactors: Array.isArray(parsed.factors) ? parsed.factors : [],
      };
    } catch (err) {
      console.warn("OpenAI analysis failed, falling back to rule-based trust evaluator:", err);
    }
  }

  // Fallback: Deterministic Rule-Based Trust Evaluator
  return evaluateRuleBasedTrust(pageText, portalUrl, officialDomain);
}

export function evaluateRuleBasedTrust(
  pageText: string,
  portalUrl: string,
  officialDomain?: string
): DetectionAnalysis {
  const lower = pageText.toLowerCase();
  const urlLower = portalUrl.toLowerCase();

  const isOfficialDomain = urlLower.includes(".gov.ng") || (officialDomain && urlLower.includes(officialDomain.toLowerCase()));
  const feeRequested = lower.includes("processing fee") || lower.includes("application fee") || lower.includes("pay to account") || lower.includes("remita fee");
  const freeEmail = lower.includes("@gmail.com") || lower.includes("@yahoo.com") || lower.includes("@hotmail.com");
  const hasRecruitmentKeywords = lower.includes("recruitment") || lower.includes("vacancies") || lower.includes("careers") || lower.includes("application form") || lower.includes("shortlisted candidates");

  const redFlags: string[] = [];
  if (feeRequested) redFlags.push("Application fee requested (Public service recruitment is free)");
  if (freeEmail) redFlags.push("Free/generic email address found in official notice");
  if (!isOfficialDomain) redFlags.push("Source portal does not use verified .gov.ng domain");

  let score = 50;
  if (isOfficialDomain) score += 35;
  if (!feeRequested) score += 10;
  if (!freeEmail) score += 5;
  if (feeRequested) score = Math.max(10, score - 60);

  const classification: "REAL" | "FAKE" | "UNCERTAIN" =
    score >= 75 ? "REAL" : score < 40 ? "FAKE" : "UNCERTAIN";

  return {
    isRecruitment: Boolean(hasRecruitmentKeywords),
    title: "Civil Service Recruitment Notice",
    positions: "Various General Cadre Vacancies",
    deadline: "See Official Gazette",
    requirements: "Valid Nigerian National Identification Number (NIN), educational credentials.",
    confidenceScore: score,
    aiClassification: classification,
    aiConfidence: 85,
    redFlags,
    confidenceFactors: [
      { label: "Official .gov.ng Domain Match", passed: isOfficialDomain },
      { label: "Zero Application Fees", passed: !feeRequested },
      { label: "No Third-Party Free Emails", passed: !freeEmail },
      { label: "Recruitment Language Detected", passed: Boolean(hasRecruitmentKeywords) },
    ],
  };
}
