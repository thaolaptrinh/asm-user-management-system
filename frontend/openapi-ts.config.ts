// @ts-nocheck - Type errors from @hey-api/openapi-ts definitions; works at runtime
import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "./openapi.json",
  output: "./src/client",

  plugins: [
    // HTTP client (Fetch API)
    "@hey-api/client-fetch",

    // SDK: service classes per tag (Login, Users, Items, etc.)
    {
      name: "@hey-api/sdk",
      operations: {
        strategy: "byTags",
        containerName: { name: "{{name}}Service", casing: "PascalCase" },
        methodName: { casing: "camelCase" },
        nesting: "operationId",
        nestingDelimiters: /[-]/,
      },
    },

    // Schemas (Zod validation, JSON output)
    {
      name: "@hey-api/schemas",
      output: "json",
    },
  ],
})
