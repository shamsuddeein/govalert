import { describe, expect, it } from "vitest";
import {
  validateAndSanitizeAgency,
  validateAndSanitizeJob,
  validateAndSanitizeSystemStatus,
  validateAndSanitizeVerification,
} from "./api";

describe("API trust-data mappers", () => {
  it("rejects absent job, agency, system, and verification payloads", () => {
    expect(validateAndSanitizeJob(null)).toBeNull();
    expect(validateAndSanitizeAgency(null)).toBeNull();
    expect(validateAndSanitizeSystemStatus(null)).toBeNull();
    expect(validateAndSanitizeVerification(null)).toBeNull();
  });

  it("uses unknown states rather than optimistic trust defaults", () => {
    const job = validateAndSanitizeJob({ ref: "101", title: "Analyst role" });
    const agency = validateAndSanitizeAgency({ id: 42, acronym: "FIRS" });
    const verification = validateAndSanitizeVerification({ ref: "101" });

    expect(job?.status).toBe("unknown");
    expect(job?.confidence_score).toBeUndefined();
    expect(job?.portal_status).toBe("unknown");
    expect(agency?.status).toBe("unknown");
    expect(agency?.vetted_score).toBeNull();
    expect(verification?.ai_classification).toBe("UNCERTAIN");
    expect(verification?.confidence_score).toBeNull();
    expect(verification?.is_verified).toBeNull();
  });
});
