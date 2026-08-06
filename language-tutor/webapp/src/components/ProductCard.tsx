"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { Product } from "@/lib/products";

const ACCENT_CLASS: Record<Product["accent"], string> = {
  gold: "product-card--gold",
  teal: "product-card--teal",
  violet: "product-card--violet",
  rose: "product-card--rose",
};

export default function ProductCard({ product }: { product: Product }) {
  const accent = ACCENT_CLASS[product.accent];
  const inner = (
    <>
      <div className="product-card-glow" aria-hidden />
      {product.badge && <span className="product-card-badge">{product.badge}</span>}
      <p className="product-card-kicker">{product.tagline}</p>
      <h3 className="product-card-title">{product.name}</h3>
      <p className="product-card-desc">{product.description}</p>
      <ul className="product-card-features">
        {product.features.map((f) => (
          <li key={f}>{f}</li>
        ))}
      </ul>
      <span className="product-card-cta">
        Open
        <ArrowUpRight className="h-4 w-4" />
      </span>
    </>
  );

  if (product.external) {
    return (
      <a
        href={product.href}
        target="_blank"
        rel="noopener noreferrer"
        className={`product-card ${accent}`}
      >
        {inner}
      </a>
    );
  }

  return (
    <Link href={product.href} className={`product-card ${accent}`}>
      {inner}
    </Link>
  );
}
