import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Metodos } from './metodos';

describe('Metodos', () => {
  let component: Metodos;
  let fixture: ComponentFixture<Metodos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Metodos]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Metodos);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
