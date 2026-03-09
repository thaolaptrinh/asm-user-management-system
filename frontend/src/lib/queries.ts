import { useQuery } from "@tanstack/react-query"
import { items } from "@/client/sdk.gen"

export function useItems(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ["items", skip, limit],
    queryFn: () =>
      items
        .listItems({ query: { skip, limit }, throwOnError: true })
        .then((r) => r.data),
  })
}
