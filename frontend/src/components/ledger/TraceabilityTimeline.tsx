import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { CheckCircle, Clock, FileText, Truck, AlertTriangle } from "lucide-react";

// Types matching backend
enum TransactionType {
  SOWING = "SOWING",
  INSPECTION = "INSPECTION",
  HARVEST = "HARVEST",
  QA_PASS = "QA_PASS",
  CERTIFICATION = "CERTIFICATION",
  TRANSFER = "TRANSFER"
}

interface Transaction {
  id: string;
  type: TransactionType;
  timestamp: string;
  data: any;
  sender: string;
  receiver?: string;
  signature?: string;
}

interface Block {
  index: number;
  timestamp: string;
  transactions: Transaction[];
  prev_hash: string;
  merkle_root: string;
  validator: string;
  hash: string;
}

// Mock Data Service
const mockBlockchainData: Block[] = [
  {
    index: 0,
    timestamp: new Date(Date.now() - 10000000).toISOString(),
    transactions: [
      {
        id: "0",
        type: TransactionType.SOWING,
        timestamp: new Date(Date.now() - 10000000).toISOString(),
        data: { message: "Genesis Block" },
        sender: "SYSTEM",
        receiver: "SYSTEM"
      }
    ],
    prev_hash: "0",
    merkle_root: "a1b2c3d4",
    validator: "SYSTEM",
    hash: "0000aaaa"
  },
  {
    index: 1,
    timestamp: new Date(Date.now() - 8000000).toISOString(),
    transactions: [
      {
        id: "tx-1",
        type: TransactionType.SOWING,
        timestamp: new Date(Date.now() - 8000000).toISOString(),
        data: { lot_id: "LOT-2024-001", crop: "Rice", variety: "IR64" },
        sender: "Farmer John",
        receiver: "Coop"
      }
    ],
    prev_hash: "0000aaaa",
    merkle_root: "e5f6g7h8",
    validator: "node1",
    hash: "0001bbbb"
  },
  {
    index: 2,
    timestamp: new Date(Date.now() - 6000000).toISOString(),
    transactions: [
      {
        id: "tx-2",
        type: TransactionType.INSPECTION,
        timestamp: new Date(Date.now() - 6000000).toISOString(),
        data: { lot_id: "LOT-2024-001", result: "Pass", notes: "Healthy growth" },
        sender: "Inspector Alice",
        receiver: "Certifier"
      }
    ],
    prev_hash: "0001bbbb",
    merkle_root: "i9j0k1l2",
    validator: "certifier1",
    hash: "0002cccc"
  },
  {
    index: 3,
    timestamp: new Date(Date.now() - 4000000).toISOString(),
    transactions: [
      {
        id: "tx-3",
        type: TransactionType.HARVEST,
        timestamp: new Date(Date.now() - 4000000).toISOString(),
        data: { lot_id: "LOT-2024-001", quantity: 5000, quality: "A" },
        sender: "Farmer John",
        receiver: "Storage"
      }
    ],
    prev_hash: "0002cccc",
    merkle_root: "m3n4o5p6",
    validator: "node1",
    hash: "0003dddd"
  },
  {
    index: 4,
    timestamp: new Date(Date.now() - 2000000).toISOString(),
    transactions: [
      {
        id: "tx-4",
        type: TransactionType.QA_PASS,
        timestamp: new Date(Date.now() - 2000000).toISOString(),
        data: { lot_id: "LOT-2024-001", qa_score: 99.5 },
        sender: "QA Lab",
        receiver: "Certifier"
      }
    ],
    prev_hash: "0003dddd",
    merkle_root: "q7r8s9t0",
    validator: "certifier1",
    hash: "0004eeee"
  }
];

export function TraceabilityTimeline() {
  const [blocks] = useState<Block[]>(mockBlockchainData);
  const [selectedBlock, setSelectedBlock] = useState<Block | null>(null);
  const [verificationStatus, setVerificationStatus] = useState<"idle" | "verifying" | "valid" | "invalid">("idle");

  const verifyChain = async () => {
    setVerificationStatus("verifying");
    // Simulate verification delay
    setTimeout(() => {
      // In a real app, we would recalculate hashes here.
      // For now, we assume the mock data is valid.
      setVerificationStatus("valid");
    }, 1500);
  };

  const getIcon = (type: TransactionType) => {
    switch (type) {
      case TransactionType.SOWING: return <FileText className="h-4 w-4" />;
      case TransactionType.INSPECTION: return <CheckCircle className="h-4 w-4" />;
      case TransactionType.HARVEST: return <Truck className="h-4 w-4" />;
      case TransactionType.QA_PASS: return <CheckCircle className="h-4 w-4 text-green-500" />;
      case TransactionType.CERTIFICATION: return <Badge className="bg-blue-500">CERT</Badge>;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Seed Traceability Ledger</h1>
        <Button onClick={verifyChain} variant={verificationStatus === "valid" ? "outline" : "default"}>
          {verificationStatus === "idle" && "Verify Chain Integrity"}
          {verificationStatus === "verifying" && "Verifying..."}
          {verificationStatus === "valid" && <><CheckCircle className="mr-2 h-4 w-4 text-green-500" /> Chain Verified</>}
          {verificationStatus === "invalid" && <><AlertTriangle className="mr-2 h-4 w-4 text-red-500" /> Integrity Failed</>}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Blockchain Timeline</CardTitle>
            <CardDescription>Immutable record of seed certification events</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
                {blocks.map((block) => (
                  <div key={block.hash} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active cursor-pointer" onClick={() => setSelectedBlock(block)}>

                    {/* Icon/Dot */}
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-slate-300 group-hover:bg-slate-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                      <Clock className="h-5 w-5 text-white" />
                    </div>

                    {/* Content Card */}
                    <Card className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 ${selectedBlock?.hash === block.hash ? 'border-primary ring-1 ring-primary' : ''}`}>
                      <div className="flex justify-between items-start mb-2">
                        <Badge variant="outline">Block #{block.index}</Badge>
                        <span className="text-xs text-muted-foreground">{new Date(block.timestamp).toLocaleDateString()}</span>
                      </div>
                      <div className="space-y-2">
                        {block.transactions.map(tx => (
                          <div key={tx.id} className="flex items-center gap-2 text-sm">
                            {getIcon(tx.type)}
                            <span className="font-medium">{tx.type}</span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-2 text-xs text-muted-foreground truncate">
                        Hash: {block.hash.substring(0, 10)}...
                      </div>
                    </Card>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Block Details</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedBlock ? (
                <div className="space-y-4">
                  <div>
                    <span className="text-sm font-semibold text-muted-foreground">Block Hash</span>
                    <p className="font-mono text-xs break-all bg-muted p-2 rounded">{selectedBlock.hash}</p>
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-muted-foreground">Previous Hash</span>
                    <p className="font-mono text-xs break-all bg-muted p-2 rounded">{selectedBlock.prev_hash}</p>
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-muted-foreground">Merkle Root</span>
                    <p className="font-mono text-xs break-all bg-muted p-2 rounded">{selectedBlock.merkle_root}</p>
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-muted-foreground">Validator</span>
                    <p className="text-sm">{selectedBlock.validator}</p>
                  </div>
                  <Separator />
                  <div>
                    <span className="text-sm font-semibold text-muted-foreground">Transactions ({selectedBlock.transactions.length})</span>
                    <div className="mt-2 space-y-2">
                      {selectedBlock.transactions.map(tx => (
                        <div key={tx.id} className="bg-muted/50 p-2 rounded text-sm">
                          <div className="flex justify-between">
                            <span className="font-bold">{tx.type}</span>
                            <span className="text-xs text-muted-foreground">{new Date(tx.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <div className="mt-1 text-xs">
                            From: {tx.sender}<br/>
                            To: {tx.receiver || "N/A"}
                          </div>
                          <div className="mt-1 text-xs font-mono bg-background p-1 rounded">
                            {JSON.stringify(tx.data, null, 2)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  Select a block to view details
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>QR Code</CardTitle>
              <CardDescription>Scan to verify lot authenticity</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
               {selectedBlock ? (
                 <>
                   <div className="bg-white p-4 rounded shadow-sm border mb-4">
                     {/* Placeholder for QR Code */}
                     <img
                       src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(`https://bijmantra.com/verify/${selectedBlock.transactions[0]?.data?.lot_id || 'unknown'}`)}`}
                       alt="QR Code"
                       className="w-32 h-32"
                     />
                   </div>
                   <p className="text-xs text-center text-muted-foreground">
                     Lot ID: {selectedBlock.transactions[0]?.data?.lot_id || 'N/A'}
                   </p>
                 </>
               ) : (
                 <div className="text-center text-muted-foreground py-8">
                   Select a block to generate QR
                 </div>
               )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default TraceabilityTimeline;
