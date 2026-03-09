"use client"

import { useQueryClient } from "@tanstack/react-query"
import type { ColumnDef } from "@tanstack/react-table"
import { MoreHorizontal } from "lucide-react"
import type { ItemPublic } from "@/client"
import { items as itemsApi } from "@/client/sdk.gen"
import { DataTable } from "@/components/data-table"
import AddItem from "@/components/items/AddItem"
import PendingItems from "@/components/pending/PendingItems"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useItems } from "@/lib/queries"

export default function ItemsPage() {
  const { data: response, isLoading } = useItems(0, 100)
  const queryClient = useQueryClient()
  const items = response?.data ?? []

  const handleDelete = async (id: string) => {
    try {
      await itemsApi.deleteItem({
        path: { item_id: id },
        throwOnError: true,
      })
      queryClient.invalidateQueries({ queryKey: ["items"] })
    } catch (error) {
      console.error("Delete failed:", error)
    }
  }

  const columns: ColumnDef<ItemPublic>[] = [
    {
      accessorKey: "id",
      header: "ID",
      cell: ({ row }) => (
        <span className="font-mono text-xs">{row.getValue("id")}</span>
      ),
    },
    {
      accessorKey: "title",
      header: "Title",
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => row.getValue("description") || "-",
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onSelect={() => handleDelete(row.original.id)}
            >
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ]

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
