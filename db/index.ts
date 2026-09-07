import { createClient } from "@libsql/client/web";
import { drizzle } from "drizzle-orm/libsql";
import * as schema from "./schema";

const DEFAULT_TURSO_URL = "libsql://alert-shamsuddeein.aws-eu-west-1.turso.io";
const DEFAULT_TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODg3Mzc5NzgsImlkIjoiMDFhMDc5MTctM2EwMS03YWRkLWEzYzAtZGRkYzY5YzA3NTY3Iiwia2lkIjoicXhUVnhLc3dPX3RIb1hrNkxfNUFSZW1mSmIyUVFpaTdOQ2hMM3diZ1RhMCIsInJpZCI6ImZhZTAxOWNkLTgzN2MtNDM3Yi1hOTA5LTU2YzQ0ZDQ1NmUyOCJ9.-RHNptmc-ulJnZD-gokDHNn9_vhpLlg-qH1lVjUaPes8zh3PsWHMdwHxZT3MaSayFbFgkTqXPPJyRGHnqn5nDw";

const url = process.env.TURSO_DATABASE_URL || DEFAULT_TURSO_URL;
const authToken = process.env.TURSO_AUTH_TOKEN || (url.startsWith("libsql:") || url.startsWith("https:") ? DEFAULT_TURSO_TOKEN : undefined);

export const client = createClient({
  url,
  authToken,
});

export const db = drizzle(client, { schema });
export * from "./schema";
