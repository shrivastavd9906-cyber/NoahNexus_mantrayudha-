from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="NovaMart Agent Mock API")

class ChatRequest(BaseModel):
    user_input: str

@app.post("/chat")
def mock_chat(req: ChatRequest):
    inp = req.user_input.lower()
    
    if "nm1042" in inp:
        return {
            "terminal_move": "ANSWER",
            "intents": ["track_delivery"],
            "reasoning_scratchpad": "Order NM1042 verified in database. Status is 'out_for_delivery' with estimated arrival today at 6 PM.",
            "verification_data": {"order_id": "NM1042", "status": "out_for_delivery", "eta": "Oct 03, 6 PM"},
            "final_response": "Your order NM1042 is currently out for delivery and is estimated to arrive by Oct 03, 6 PM."
        }
    elif "nm4421" in inp or "never received" in inp:
        return {
            "terminal_move": "ESCALATE",
            "intents": ["refund_request", "delivery_dispute"],
            "reasoning_scratchpad": "Contradiction detected: Customer claims non-delivery, but DB record indicates OTP-verified delivery on Sep 28.",
            "verification_data": {"order_id": "NM4421", "status": "delivered", "otp_verified": True},
            "final_response": "I see that order NM4421 was marked delivered via OTP verification on September 28. Because of this delivery log mismatch, I have escalated your request to our human support manager under ticket #ST-7701."
        }
    elif "ignore" in inp or "50,000" in inp or "50000" in inp:
        return {
            "terminal_move": "ESCALATE",
            "intents": ["unauthorized_command"],
            "reasoning_scratchpad": "Prompt injection / policy override attempt detected in customer input. Command refused.",
            "verification_data": {"injection_flag": True, "reason": "Attempted administrative refund override"},
            "final_response": "I cannot fulfill this request as it violates core policy constraints. Your session has been flagged and escalated to support."
        }
    else:
        return {
            "terminal_move": "ASK",
            "intents": ["return_request"],
            "reasoning_scratchpad": "Ambiguous request: Customer specified 'headphones', but holds two separate headphone orders (NM-1101 and NM-2230).",
            "verification_data": {"matching_orders": ["NM-1101 (Sony WH-1000)", "NM-2230 (Boat Rockerz)"]},
            "final_response": "You have two recent headphone orders: Order NM-1101 (Sony WH-1000) and Order NM-2230 (Boat Rockerz). Could you specify which order you would like to return?"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)