import crypto from "crypto";
import { client } from "../db/index";

function verifyDjangoPassword(password: string, encoded: string): boolean {
  if (!encoded || !encoded.includes("$")) return false;
  const parts = encoded.split("$");
  if (parts.length !== 4) return false;
  const [algorithm, iterationsStr, salt, hash] = parts;
  if (algorithm !== "pbkdf2_sha256") return false;
  const iterations = parseInt(iterationsStr, 10);
  const computed = crypto.pbkdf2Sync(password, salt, iterations, 32, "sha256").toString("base64");
  return computed === hash;
}

async function main() {
  const res = await client.execute("SELECT id, username, email, password FROM auth_user");
  for (const user of res.rows) {
    const p = String(user.password || "");
    const isFormPass = verifyDjangoPassword("formpassword", p);
    const isAdminPass = verifyDjangoPassword("adminpassword123", p);
    const isPass = verifyDjangoPassword("password", p);
    const isPass123 = verifyDjangoPassword("Password123!", p);
    console.log(`User ${user.username} (${user.email}):`, {
      formpassword: isFormPass,
      adminpassword123: isAdminPass,
      password: isPass,
      Password123: isPass123,
    });
  }
}

main().catch(console.error);
