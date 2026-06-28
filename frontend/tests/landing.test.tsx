import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import LandingPage from "@/app/page";

describe("LandingPage", () => {
  it("renders the heading", () => {
    render(<LandingPage />);
    expect(screen.getByText("UPSC OS")).toBeInTheDocument();
  });

  it("renders the get started link", () => {
    render(<LandingPage />);
    const link = screen.getByText("Get Started");
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/login");
  });
});
