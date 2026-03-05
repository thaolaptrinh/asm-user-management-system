"use client"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import ChangePassword from "@/components/user-settings/ChangePassword"
import DeleteAccount from "@/components/user-settings/DeleteAccount"
import UserInformation from "@/components/user-settings/UserInformation"

export default function SettingsPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-4">
          <div className="flex flex-col gap-6">
            <UserInformation />
            <DeleteAccount />
          </div>
        </TabsContent>

        <TabsContent value="password" className="mt-4">
          <ChangePassword />
        </TabsContent>
      </Tabs>
    </div>
  )
}
