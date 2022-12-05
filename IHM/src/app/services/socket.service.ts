import { Injectable } from '@angular/core';
import {Socket} from "ngx-socket-io";
import {map} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class SocketService {


  constructor(private socket: Socket) {
  }


  getData(){
    return this.socket.fromEvent("get_data").pipe(map((data:any) => data))
  }

  getLog(){
    return this.socket.fromEvent("get_log").pipe(map((log:any) => log))
  }




}
