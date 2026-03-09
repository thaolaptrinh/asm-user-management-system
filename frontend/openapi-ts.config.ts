import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "./openapi.json",
  output: {
    path: "./src/client",
    clean: false,
  },
  plugins: [
    {
      name: "@hey-api/client-next",
      runtimeConfigPath: "../hey-api.ts",
    },
    {
      name: "@hey-api/sdk",
      operations: {
        strategy: "byTags",
        containerName: { casing: "camelCase" },
        methodName: { casing: "camelCase" },
      },
    },
    {
      name: "@hey-api/schemas",
      output: "zod",
    },
  ],
})
