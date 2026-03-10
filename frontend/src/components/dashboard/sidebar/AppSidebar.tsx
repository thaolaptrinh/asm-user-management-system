"use client"
import { Home, Users } from "lucide-react"

import { SidebarAppearance } from "@/components/common/appearance"
import { Logo } from "@/components/common/logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import { useAuth } from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

const items: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  { icon: Users, title: "Users", path: "/users" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
