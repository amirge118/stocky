"use client"

import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { updateStock } from "@/lib/api/stocks"
import { useToast } from "@/hooks/use-toast"
import type { Stock } from "@/types/stock"

const stockUpdateSchema = z.object({
  name: z.string().min(1, "Name is required").max(255, "Name must be 255 characters or less"),
  exchange: z.enum(["NASDAQ", "NYSE", "AMEX", "OTC"], "Please select an exchange"),
  sector: z.string().max(100, "Sector must be 100 characters or less").optional().nullable(),
})

type StockUpdateForm = {
  name: string
  exchange: "NASDAQ" | "NYSE" | "AMEX" | "OTC"
  sector?: string | null
}

export interface EditStockDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  stock: Stock
  onSuccess?: () => void
}

export function EditStockDialog({
  open,
  onOpenChange,
  stock,
  onSuccess,
}: EditStockDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm({
    resolver: zodResolver(stockUpdateSchema),
    defaultValues: {
      name: stock.name,
      exchange: stock.exchange as StockUpdateForm["exchange"],
      sector: stock.sector,
    },
  })

  const exchangeValue = watch("exchange")

  // Reset form when stock changes
  useEffect(() => {
    if (open && stock) {
      reset({
        name: stock.name,
        exchange: stock.exchange as StockUpdateForm["exchange"],
        sector: stock.sector,
      })
    }
  }, [stock, open, reset])

  const mutation = useMutation({
    mutationFn: (data: StockUpdateForm) => updateStock(stock.symbol, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] })
      toast({
        title: "Success",
        description: "Stock updated successfully",
      })
      setIsSubmitting(false)
      onOpenChange(false)
      onSuccess?.()
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to update stock",
        variant: "destructive",
      })
      setIsSubmitting(false)
    },
  })

  const onSubmit = async (data: StockUpdateForm) => {
    setIsSubmitting(true)
    mutation.mutate(data)
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && !isSubmitting) {
      reset()
    }
    onOpenChange(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Stock</DialogTitle>
          <DialogDescription>
            Update stock information. Symbol cannot be changed.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="symbol">Symbol</Label>
              <Input
                id="symbol"
                value={stock.symbol}
                disabled
                className="bg-muted"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="name">
                Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                {...register("name")}
                className={errors.name ? "border-destructive" : ""}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="exchange">
                Exchange <span className="text-destructive">*</span>
              </Label>
              <Select
                value={exchangeValue}
                onValueChange={(value) => setValue("exchange", value as StockUpdateForm["exchange"])}
              >
                <SelectTrigger
                  id="exchange"
                  className={errors.exchange ? "border-destructive" : ""}
                >
                  <SelectValue placeholder="Select exchange" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="NASDAQ">NASDAQ</SelectItem>
                  <SelectItem value="NYSE">NYSE</SelectItem>
                  <SelectItem value="AMEX">AMEX</SelectItem>
                  <SelectItem value="OTC">OTC</SelectItem>
                </SelectContent>
              </Select>
              {errors.exchange && (
                <p className="text-sm text-destructive">{errors.exchange.message}</p>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="sector">Sector (Optional)</Label>
              <Input
                id="sector"
                {...register("sector")}
                className={errors.sector ? "border-destructive" : ""}
              />
              {errors.sector && (
                <p className="text-sm text-destructive">{errors.sector.message}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Updating..." : "Update Stock"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
