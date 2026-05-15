import { NextResponse } from "next/server";

import { getVendor } from "@/data/get-dataset";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const vendor = getVendor(id);
  if (!vendor) {
    return NextResponse.json({ error: "Vendor not found" }, { status: 404 });
  }
  return NextResponse.json(vendor);
}
