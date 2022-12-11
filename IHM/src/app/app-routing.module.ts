import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {SessionComponent} from "./components/session/session.component";
import {InterfaceComponent} from "./components/interface/interface.component";

const routes: Routes = [
  { path: 'IHM', component: InterfaceComponent },
  { path: '', component: SessionComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
