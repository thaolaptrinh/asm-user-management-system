"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
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

const formSchema = z.object({
  email: z.string().email(),
})

type FormData = z.infer<typeof formSchema>

export default function RecoverPasswordPage() {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
    },
  })

  const mutation = useMutation({
    mutationFn: async (email: string) => {
      const { data } = await auth.recoverPassword({
        path: { email },
      })

      if (!data) {
        throw new Error("Failed to send recovery email")
      }

      return data
    },

    onSuccess: () => {
      toast.success("Password recovery email sent successfully")
      form.reset()
    },

    onError: (error: Error) => {
      toast.error(error.message)
    },
  })

  const onSubmit = (data: FormData) => {
    if (mutation.isPending) return
    mutation.mutate(data.email)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Password Recovery</h1>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
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

          <LoadingButton
            type="submit"
            className="w-full"
            loading={mutation.isPending}
          >
            Continue
          </LoadingButton>
        </form>
      </Form>

      <div className="text-center text-sm">
        Remember your password?{" "}
        <Link href="/login" className="underline underline-offset-4">
          Log in
        </Link>
      </div>
    </div>
  )
}
