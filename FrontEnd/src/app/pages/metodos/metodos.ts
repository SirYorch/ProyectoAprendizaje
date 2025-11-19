import { Component } from '@angular/core';
import { PrediccionService, ProductPrediction } from '../../services/prediccion';
import { finalize } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-metodos',
  imports: [FormsModule, CommonModule],
  templateUrl: './metodos.html',
  styleUrl: './metodos.css',
})
export class Metodos {

  // FORMULARIO
  producto: string = '';
  fecha: string = '';

  // RESPUESTAS
  respuesta: string = '';
  respuestaModelo: any = null;

  // LOADING Y ERRORES
  loading = false;
  error = '';

  predicciones: ProductPrediction[] = []

  constructor(private api: PrediccionService) {}
  predecirStockProducto() {
    this.limpiarPredicciones()
    if (!this.producto || !this.fecha) {
      this.error = "Producto y fecha son obligatorios";
      return;
    }

    this.reset();
    this.loading = true;

    this.api.predictProductStock({
      product_name: this.producto,
      predict_date: this.fecha
    })
    .pipe(finalize(() => this.loading = false))
    .subscribe(
      r => {
        this.respuesta = `Stock esperado: ${r.predicted_stock}`;
        this.respuestaModelo = r;
      },
      () => this.error = "Error conectando al servidor"
    );
  }

  predecirFechaCompleta() {
    this.limpiarPredicciones()
    if (!this.fecha) {
      this.error = "La fecha es obligatoria";
      return;
    }

    this.reset();
    this.loading = true;

    this.api.predictDate({ prediction_date: this.fecha })
      .pipe(finalize(() => this.loading = false))
      .subscribe(
        r => {
          console.log(r)
           this.respuesta = `Total productos predichos: ${r.total_products}`;
        this.respuestaModelo = r;
          this.predicciones = r.predictions;   // ← AQUÍ
        },
        () => this.error = "Error en predicción por fecha"
      );
  }

  productosEnRiesgo() {
    this.limpiarPredicciones()
    this.reset();
    this.loading = true;

    this.api.predictOutOfStock()
      .pipe(finalize(() => this.loading = false))
      .subscribe(
        r => {
          console.log(r)
          this.respuesta =
            `Productos en riesgo: ${r.total_products} — Fecha riesgo: ${r.risk_date}`;
          this.respuestaModelo = r;
          this.predicciones = r.products_at_risk
        },
        () => this.error = "Error obteniendo productos en riesgo"
      );
  }
  predecirAgotamiento() {
    this.limpiarPredicciones()
    if (!this.producto) {
      this.error = "Escribe un producto";
      return;
    }

    this.reset();
    this.loading = true;

    this.api.predictProductOutOfStock({ product_name: this.producto })
      .pipe(finalize(() => this.loading = false))
      .subscribe(
        r => {
          this.respuesta = `Se agotará el ${r.predicted_out_date}`;
          this.respuestaModelo = r;
        },
        () => this.error = "Error prediciendo agotamiento"
      );
  }

  subirCSV(event: any) {
    this.limpiarPredicciones()
    const file = event.target.files[0];
    if (!file) return;

    this.reset();
    this.loading = true;

    this.api.uploadAndRetrain(file)
      .pipe(finalize(() => this.loading = false))
      .subscribe(
        r => {
          console.log(r)
          this.respuesta =
            `Modelo reentrenado.`;
          this.respuestaModelo = r;
        },
        () => this.error = "Error subiendo CSV"
      );
  }

  // RESET
  reset() {
    this.respuesta = '';
    this.respuestaModelo = null;
    this.error = '';
  }

  limpiarPredicciones(){
    this.predicciones = []
  }
}
