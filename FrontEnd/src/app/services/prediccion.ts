import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const API_URL = 'http://34.9.45.83:8000';

export interface ChatRequest {
  message: string;
}
export interface ChatResponse {
  success: boolean;
  message: string;
}

export interface PredictProductStockRequest {
  product_name: string;
  predict_date: string;
}
export interface ProductStockResponse {
  success: boolean;
  message: string;
  product_name: string;
  prediction_date: string;
  predicted_stock: number;
  current_stock: number;
}

export interface PredictDateRequest {
  prediction_date: string;
}
export interface ProductPrediction {
  product_name: string;
  predicted_stock: number;
}
export interface DatePredictionResponse {
  success: boolean;
  message: string;
  prediction_date: string;
  total_products: number;
  predictions: ProductPrediction[];
}

export interface ProductOutOfStockInfo {
  product_name: string;
  predicted_stock: number;
  current_stock: number;
}
export interface OutOfStockResponse {
  success: boolean;
  message: string;
  total_products: number;
  risk_date: string;
  products_at_risk: ProductOutOfStockInfo[];
}

export interface PredictProductOutOfStockRequest {
  product_name: string;
}
export interface ProductOutOfStockResponse {
  success: boolean;
  message: string;
  product_name: string;
  predicted_out_date: string;
  predictions: ProductPrediction[];
}

export interface RetrainResponse {
  success: boolean;
  message: string;
  filename: string;
  rows_processed: number;
  rows_inserted: number;
  model_retrained: boolean;
  previous_accuracy: number | null;
  new_accuracy: number | null;
  training_time_seconds: number;
}

@Injectable({
  providedIn: 'root',
})
export class PrediccionService {
  constructor(private http: HttpClient) {}

  predictOutOfStock(): Observable<OutOfStockResponse> {
    return this.http.get<OutOfStockResponse>(
      `${API_URL}/api/predict/out-of-stock`
    );
  }

  predictProductStock(
    data: PredictProductStockRequest
  ): Observable<ProductStockResponse> {
    return this.http.post<ProductStockResponse>(
      `${API_URL}/api/predict/product-stock`,
      data
    );
  }

  predictDate(data: PredictDateRequest): Observable<DatePredictionResponse> {
    return this.http.post<DatePredictionResponse>(
      `${API_URL}/api/predict/date`,
      data
    );
  }

  predictProductOutOfStock(
    data: PredictProductOutOfStockRequest
  ): Observable<ProductOutOfStockResponse> {
    return this.http.post<ProductOutOfStockResponse>(
      `${API_URL}/api/predict/product-out-of-stock`,
      data
    );
  }

  chat(data: ChatRequest): Observable<ChatResponse> {
    console.log(data);
    return this.http.post<ChatResponse>(`${API_URL}/api/chat`, data);
  }

  uploadAndRetrain(file: File): Observable<RetrainResponse> {
    const form = new FormData();
    form.append('file', file);

    return this.http.post<RetrainResponse>(
      `${API_URL}/api/upload/retrain`,
      form
    );
  }
}
