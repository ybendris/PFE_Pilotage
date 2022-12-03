import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { AppComponent } from './app.component';
import { TestComponent } from './components/test/test.component';
import {SocketIoConfig, SocketIoModule} from "ngx-socket-io";
import { CommandeComponent } from './components/commande/commande.component';

const config: SocketIoConfig = { url: "http://localhost:5000", options: {} };

@NgModule({
  declarations: [
    AppComponent,
    TestComponent,
    CommandeComponent,
  ],
  imports: [
    BrowserModule,
    FormsModule,
    SocketIoModule.forRoot(config)
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
