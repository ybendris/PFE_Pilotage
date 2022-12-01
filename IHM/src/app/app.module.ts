import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { TestComponent } from './components/test/test.component';
import {SocketIoConfig, SocketIoModule} from "ngx-socket-io";

const config: SocketIoConfig = { url: "http://localhost:5000", options: {} };

@NgModule({
  declarations: [
    AppComponent,
    TestComponent
  ],
  imports: [
    BrowserModule,
    SocketIoModule.forRoot(config)
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
