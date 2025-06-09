const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function loginUser(email: string, password: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || errorData.message || "Login failed");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Login error:", error);
    throw error;
  }
}

export async function signupUser(username: string, email: string, password: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || errorData.message || "Signup failed");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Signup error:", error);
    throw error;
  }
}