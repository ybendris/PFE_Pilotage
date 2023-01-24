import { Injectable } from '@angular/core';
import {BehaviorSubject} from "rxjs";
import {Data} from "../models/data.model";

@Injectable({
  providedIn: 'root'
})
export class ChartDataService {

  private _data = new BehaviorSubject<Data<unknown>>({
    type: "",
    expediteur: "",
    paquet: "",
    msg: {}
  });
  data$ = this._data.asObservable();

  constructor() { }

  //Met à jour et émet les nouvelles données au graphique
  updateData(data: Data<unknown>) {
    console.log("updateData ", data)
    this._data.next(data);
  }

}
