import { useState, useCallback } from "react";
import { MagnifyingGlass, ArrowRight } from "@phosphor-icons/react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const SUGGESTED_COMPANIES = [
  "Shopify",
  "Tesla",
  "Netflix",
  "Stripe",
  "Airbnb",
  "Spotify",
  "Datadog",
  "Cloudflare",
];

interface CompanyInputProps {
  onSubmit: (company: string) => void;
  disabled?: boolean;
}

export function CompanyInput({ onSubmit, disabled = false }: CompanyInputProps) {
  const [value, setValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);

  const filtered = value.trim()
    ? SUGGESTED_COMPANIES.filter((c) => c.toLowerCase().includes(value.toLowerCase()))
    : SUGGESTED_COMPANIES;

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (trimmed) {
      onSubmit(trimmed);
    }
  }, [value, onSubmit]);

  const handleSelect = useCallback(
    (company: string) => {
      setValue(company);
      setShowSuggestions(false);
      onSubmit(company);
    },
    [onSubmit],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Company Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="company-name"
              placeholder="Enter company name..."
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              className="pl-10"
              disabled={disabled}
              aria-label="Company name"
            />
            {showSuggestions && filtered.length > 0 && (
              <div
                className="absolute z-10 mt-1 w-full rounded-md border bg-popover shadow-md"
                role="listbox"
                aria-label="Company suggestions"
              >
                {filtered.map((company) => (
                  <button
                    key={company}
                    role="option"
                    aria-selected={false}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground transition-colors first:rounded-t-md last:rounded-b-md"
                    onMouseDown={() => handleSelect(company)}
                  >
                    {company}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button onClick={handleSubmit} disabled={disabled || !value.trim()}>
            Analyse
            <ArrowRight />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
