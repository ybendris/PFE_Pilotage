import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { AppComponent } from './app.component';
import { DataComponent } from './components/data/data.component';
import {SocketIoConfig, SocketIoModule} from "ngx-socket-io";
import { CommandeComponent } from './components/commande/commande.component';
import { AppRoutingModule } from './app-routing.module';
import { SessionComponent } from './components/session/session.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatIconModule} from "@angular/material/icon";
import {MatInputModule} from "@angular/material/input";
import {MatButtonModule} from "@angular/material/button";

const config: SocketIoConfig = { url: "http://localhost:5000", options: {} };

@NgModule({
  declarations: [
    AppComponent,
    DataComponent,
    CommandeComponent,
    SessionComponent,
    DashboardComponent,
  ],
    imports: [
        BrowserModule,
        FormsModule,
        SocketIoModule.forRoot(config),
        AppRoutingModule,
        BrowserAnimationsModule,
        MatFormFieldModule,
        MatIconModule,
        MatInputModule,
        MatButtonModule
    ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
