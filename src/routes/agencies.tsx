import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/agencies")({
  component: AgenciesLayout,
});

function AgenciesLayout() {
  return <Outlet />;
}
