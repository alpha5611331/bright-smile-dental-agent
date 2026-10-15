"use client";

import { useQueryClient } from "@tanstack/react-query";
import { LogOutIcon, MonitorIcon, MoonIcon, SunIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { api } from "@/lib/api/client";
import { LOGIN_PATH } from "@/lib/leads/queries";
import { practice } from "@/lib/practice";

function ThemeMenu() {
  const { theme, setTheme } = useTheme();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="ghost" size="icon-lg" />}>
        <SunIcon className="dark:hidden" />
        <MoonIcon className="hidden dark:block" />
        <span className="sr-only">Color theme</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuGroup>
          <DropdownMenuRadioGroup value={theme ?? "system"} onValueChange={setTheme}>
            <DropdownMenuRadioItem value="light">
              <SunIcon />
              Light
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="dark">
              <MoonIcon />
              Dark
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="system">
              <MonitorIcon />
              System
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function DashboardHeader() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const logOut = async () => {
    await api.POST("/api/auth/logout").catch(() => undefined);
    queryClient.clear(); // never leave patient data in memory after logging out
    router.replace(LOGIN_PATH);
  };

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <div className="flex flex-col leading-tight">
          <span className="font-heading text-lg font-bold">{practice.practice_name}</span>
          <span className="text-xs text-muted-foreground">Front desk</span>
        </div>
        <div className="ml-auto flex items-center gap-1">
          <ThemeMenu />
          <Button variant="ghost" size="lg" onClick={() => void logOut()}>
            <LogOutIcon data-icon="inline-start" />
            Log out
          </Button>
        </div>
      </div>
    </header>
  );
}
