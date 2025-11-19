import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgenteLlm } from './agente-llm';

describe('AgenteLlm', () => {
  let component: AgenteLlm;
  let fixture: ComponentFixture<AgenteLlm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgenteLlm]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgenteLlm);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
