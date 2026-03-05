"use client"
import { useQuery } from "@tanstack/react-query"
import { Items } from "@/client"
import { DataTable } from "@/components/data-table"
import AddItem from "@/components/items/AddItem"
import { columns } from "@/components/items/columns"
import PendingItems from "@/components/pending/PendingItems"

export default function ItemsPage() {
  const { data: response, isLoading } = useQuery({
    queryKey: ["items"],
    queryFn: () => Items.readItems({ throwOnError: true }).then((r) => r.data),
  })

  const items = response?.data ?? []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Items</h1>
      </div>

      {isLoading ? (
        <PendingItems />
      ) : (
        <>
          <AddItem />
          <DataTable columns={columns} data={items} />
        </>
      )}
    </div>
  )
}
