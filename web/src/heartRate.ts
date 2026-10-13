// Live heart rate from a Bluetooth LE strap or a watch in "broadcast HR" mode,
// via the standard Heart Rate service (0x180D) / Measurement characteristic (0x2A37).
// Web Bluetooth works in Chrome/Edge on desktop and Android; NOT on iOS (incl. Telegram's iOS web view).

/** Minimal Web Bluetooth typings — not part of TypeScript's DOM lib. */
interface BleCharacteristic extends EventTarget {
  value?: DataView
  startNotifications(): Promise<BleCharacteristic>
}
interface BleDevice extends EventTarget {
  name?: string
  gatt?: {
    connect(): Promise<{
      getPrimaryService(s: string): Promise<{ getCharacteristic(c: string): Promise<BleCharacteristic> }>
    }>
    disconnect(): void
  }
}
interface BleNavigator {
  bluetooth?: { requestDevice(o: { filters: { services: string[] }[] }): Promise<BleDevice> }
}

const bluetooth = () => (navigator as Navigator & BleNavigator).bluetooth

export const heartRateSupported = (): boolean => Boolean(bluetooth())

/** Parse a Heart Rate Measurement value: flag bit 0 selects uint8 vs uint16 BPM. */
export function parseHeartRate(value: DataView): number {
  const flags = value.getUint8(0)
  return flags & 0x01 ? value.getUint16(1, true) : value.getUint8(1)
}

export interface HeartRateConnection {
  deviceName: string
  disconnect(): void
}

/** Must be called from a user gesture (button click). */
export async function connectHeartRate(onBpm: (bpm: number) => void, onLost: () => void): Promise<HeartRateConnection> {
  const bt = bluetooth()
  if (!bt) throw new Error('Bluetooth is not available in this browser')
  const device = await bt.requestDevice({ filters: [{ services: ['heart_rate'] }] })
  if (!device.gatt) throw new Error('Device has no GATT server')
  const server = await device.gatt.connect()
  const service = await server.getPrimaryService('heart_rate')
  const characteristic = await service.getCharacteristic('heart_rate_measurement')

  const onValue = () => {
    if (characteristic.value) onBpm(parseHeartRate(characteristic.value))
  }
  characteristic.addEventListener('characteristicvaluechanged', onValue)
  device.addEventListener('gattserverdisconnected', onLost)
  await characteristic.startNotifications()

  return {
    deviceName: device.name ?? 'Heart-rate sensor',
    disconnect() {
      characteristic.removeEventListener('characteristicvaluechanged', onValue)
      device.removeEventListener('gattserverdisconnected', onLost)
      device.gatt?.disconnect()
    },
  }
}
