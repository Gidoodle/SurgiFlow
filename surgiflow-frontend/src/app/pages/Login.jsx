export default function Login() {
  const handleLogin = () => {
    localStorage.setItem("axiom_token", "dev-token");
    window.location.href = "/dashboard";
  };

  return (
    <div>
      <h1>Login</h1>
      <button onClick={handleLogin}>Login (dev)</button>
    </div>
  );
}
