import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {SessionComponent} from "./components/session/session.component";
import {DashboardComponent} from "./components/dashboard/dashboard.component";

const routes: Routes = [
  { path: 'IHM', component: DashboardComponent },
  { path: '', component: SessionComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
