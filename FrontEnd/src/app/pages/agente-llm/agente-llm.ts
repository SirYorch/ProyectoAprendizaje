import { Component } from '@angular/core';
import { PrediccionService } from '../../services/prediccion';
import { finalize } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MarkdownService, MarkdownComponent } from 'ngx-markdown';



@Component({
  selector: 'app-agente-llm',
  imports: [FormsModule, CommonModule, MarkdownComponent],
  templateUrl: './agente-llm.html',
  styleUrl: './agente-llm.css',
})
export class AgenteLlm {
  mensajes: Mensaje[] = [];

  texto: string = '';
  error:string = "";

  loading: boolean = false;

  constructor(private service: PrediccionService) {
    
  }

  enviarMensaje() {
    this.error = "";
    this.loading = true;
    this.service
      .chat({
        message: this.texto,
      })
      .pipe(
        finalize(() => {
          this.loading = false;
        })
      )
      .subscribe((api) => {
        console.log(api)
        if(!api.success) throw "Error al chatear"
        this.mensajes.push({ texto: this.texto, remitente: 'me' });
        this.texto = '';
        let textoFinal = api.message.substring(11, api.message.length-4)
        this.mensajes.push({ texto: textoFinal, remitente: 'CHAT' });
      }, (error)=>{
        this.error = error;
      });
  }
}

interface Mensaje {
  texto: string;
  remitente: string;
}
