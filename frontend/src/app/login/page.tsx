"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { loginUser } from "@/lib/auth"; // Import loginUser
import { useAuth } from "@/context/AuthContext"; // Import useAuth

const formSchema = z.object({
  email: z.string().email({ message: "Invalid email address." }),
  password: z.string().min(6, { message: "Password must be at least 6 characters." }),
});

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null); // State for error messages

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const { login } = useAuth(); // Use the useAuth hook

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsLoading(true);
    setError(null); // Clear previous errors
    try {
      const data = await loginUser(values.email, values.password);
      console.log("Login successful:", data);
      login(data.access_token); // Store token and redirect
    } catch (err: any) {
      if (err instanceof Error) {
        setError(err.message || "An unexpected error occurred.");
        console.error("Login error:", err); // Log the full error object
      } else {
        setError("An unexpected error occurred.");
        console.error("Login error:", err); // Log the full error object for non-Error types
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-950">
      <Card className="mx-auto max-w-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Login</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input placeholder="m@example.com" {...field} />
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
                      <Input type="password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button className="w-full" type="submit" disabled={isLoading}>
                {isLoading ? "Logging in..." : "Login"}
              </Button>
              <p className="text-red-500 text-sm text-center h-5">{error}</p>
            </form>
          </Form>
          <div className="mt-4 text-center text-sm">
            Don't have an account?{" "}
            <Link className="underline" href="/signup">
              Sign up
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}