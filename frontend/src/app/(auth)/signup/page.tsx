"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { auth } from "@/client/sdk.gen"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"

const formSchema = z
  .object({
    email: z.string().email(),
    full_name: z.string().min(1, { message: "Full Name is required" }),
    password: z
      .string()
      .min(1, { message: "Password is required" })
      .min(8, { message: "Password must be at least 8 characters" }),
    confirm_password: z
      .string()
      .min(1, { message: "Password confirmation is required" }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "The passwords don't match",
    path: ["confirm_password"],
  })

type FormData = z.infer<typeof formSchema>

export default function SignUpPage() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
    },
  })

  const mutation = useMutation({
    mutationFn: async (data: {
      email: string
      full_name: string
      password: string
    }) => {
      const { data: res } = await auth.register({
        body: data,
        throwOnError: true,
      })

      return res!
    },

    onSuccess: () => {
      router.push("/login?registered=true")
    },

    onError: (err: unknown) => {
      const message =
        (err instanceof Error && err.message) ||
        (typeof err === 'object' && err !== null && 'detail' in err && String(err.detail)) ||
        "Registration failed. Please try again."
      setError(message)
    },
  })

  const onSubmit = (data: FormData) => {
    if (mutation.isPending) return
    setError(null)
    const { confirm_password, ...submitData } = data
    mutation.mutate(submitData)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Create an account</h1>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Full Name</FormLabel>

                <FormControl>
                  <Input
                    data-testid="full-name-input"
                    placeholder="User"
                    type="text"
                    {...field}
                  />
                </FormControl>

                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>

                <FormControl>
                  <Input
                    data-testid="email-input"
                    placeholder="user@example.com"
                    type="email"
                    {...field}
                  />
                </FormControl>

                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>

                <FormControl>
                  <PasswordInput
                    data-testid="password-input"
                    placeholder="Password"
                    {...field}
                  />
                </FormControl>

                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="confirm_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirm Password</FormLabel>

                <FormControl>
                  <PasswordInput
                    data-testid="confirm-password-input"
                    placeholder="Confirm Password"
                    {...field}
                  />
                </FormControl>

                <FormMessage />
              </FormItem>
            )}
          />

          {error && (
            <p className="text-sm text-destructive text-center">{error}</p>
          )}

          <LoadingButton
            type="submit"
            className="w-full"
            loading={mutation.isPending}
          >
            Sign Up
          </LoadingButton>
        </form>
      </Form>

      <div className="text-center text-sm">
        Already have an account?{" "}
        <Link href="/login" className="underline underline-offset-4">
          Log in
        </Link>
      </div>
    </div>
  )
}
