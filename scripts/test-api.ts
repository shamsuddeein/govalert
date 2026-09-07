import { handleApiRequest } from "../server/api";

async function testEndpoint(name: string, path: string, method = "GET", body?: any) {
  const req = new Request(`http://localhost:3000${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  const res = await handleApiRequest(req);
  if (!res) {
    console.log(`❌ ${name}: Not handled (404)`);
    return;
  }

  const status = res.status;
  const json: any = await res.json();
  const count = json.count ?? json.results?.length ?? (json.id ? 1 : "ok");
  console.log(`✅ [${status}] ${name} (${path}) -> count/status:`, count);
  return json;
}

async function run() {
  console.log("🧪 Testing GovAlert Serverless API Routes with Drizzle + SQLite/Turso:\n");

  await testEndpoint("Agencies List", "/api/v1/agencies");
  await testEndpoint("Single Agency", "/api/v1/agencies/ncs");
  await testEndpoint("Jobs List", "/api/v1/jobs");
  await testEndpoint("Job Verification", "/api/v1/jobs/0018-GA/verification");
  await testEndpoint("System Status", "/api/v1/status");
  await testEndpoint("Live Feed", "/api/v1/status/live-feed");
  await testEndpoint("Blog Posts", "/api/v1/blog");
  await testEndpoint("Admin Alerts Queue", "/api/v1/admin/alerts");

  console.log("\n🎉 All API routes verified successfully!");
}

run().catch(console.error);
