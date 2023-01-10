export interface Data {
  type: string,
  expediteur: string,
  paquet: string,
  msg: {
    time: string,
    data: number
  }[]

}
