"use client"
import { useQuery } from "@tanstack/react-query"
import { users as usersApi } from "@/client/sdk.gen"
import AddUser from "@/components/users/AddUser"
import { columns, type UserTableData } from "@/components/users/columns"
import { DataTable } from "@/components/data-table"
import PendingUsers from "@/components/pending/PendingUsers"
import { useAuth } from "@/hooks/useAuth"

export default function UsersPage() {
  const { user } = useAuth()

  const { data: response, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () =>
      usersApi.listUsers({ throwOnError: true }).then((r) => r.data),
    enabled: !!user,
  })

  const userList: UserTableData[] = (response?.data ?? []).map((u) => ({
    ...u,
    isCurrentUser: u.email === user?.email,
  }))

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Users Management</h1>
      </div>

      {isLoading ? (
        <PendingUsers />
      ) : (
        <>
          <AddUser />
          <DataTable columns={columns} data={userList} />
        </>
      )}
    </div>
  )
}
