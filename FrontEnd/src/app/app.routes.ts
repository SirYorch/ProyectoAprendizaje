import { Routes } from '@angular/router';
import { Sobre } from './pages/sobre/sobre';
import { AgenteLlm } from './pages/agente-llm/agente-llm';
import { Metodos } from './pages/metodos/metodos';

export const routes: Routes = [
    { path: '', redirectTo: 'sobre', pathMatch: 'full' },
  { path: 'sobre', component: Sobre },
  { path: 'agente-llm', component: AgenteLlm },
  { path: 'metodos', component: Metodos }
];
