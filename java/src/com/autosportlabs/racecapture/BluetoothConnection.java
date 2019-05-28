/**
 * Race Capture App
 *
 * Copyright (C) 2014-2017 Autosport Labs
 *
 * This file is part of the Race Capture App
 *
 * This is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 * See the GNU General Public License for more details. You should
 * have received a copy of the GNU General Public License along with
 * this code. If not, see <http://www.gnu.org/licenses/>.
 */
package com.autosportlabs.racecapture;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.util.Log;

import java.util.UUID;
import java.util.Set;
import java.util.List;
import java.util.ArrayList;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.lang.reflect.Method;

/**
 * Bluetooth connection bridge for RaceCature app
 * @author brent
 *
 */
public class BluetoothConnection {
	private static final UUID SerialPortServiceClass_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

	private volatile BluetoothSocket socket;
	private volatile InputStream recv_stream;
	private volatile OutputStream send_stream;
	private volatile BufferedReader reader;
	boolean mAllowInsecureConnections = false;
	Object lock = new Object();
	
	static BluetoothConnection g_instance;
	
	private BluetoothConnection(){
	}
	
	static public BluetoothConnection createInstance(){
		if (g_instance == null){
			g_instance = new BluetoothConnection();
		}
		return g_instance;
	}
	
	private class ConnectThread extends Thread{
		
		BluetoothDevice device = null;
		String errorMessage = null;
		
        public ConnectThread(BluetoothDevice device) {
			this.device = device;
        }
        
        
        public void run(){
        	try{
	        	if ( mAllowInsecureConnections ) {
	        		Log.i("BluetoothConnection", "create socket insecure mode");
	        		Method method;
	        		method = this.device.getClass().getMethod("createRfcommSocket", new Class[] { int.class } );
	        		BluetoothConnection.this.socket = (BluetoothSocket) method.invoke(this.device, 1);  
	        	}
	        	else {
	        		Log.i("BluetoothConnection", "create socket secure mode");
	        		BluetoothConnection.this.socket = this.device.createRfcommSocketToServiceRecord( SerialPortServiceClass_UUID );
	        	}
	            if (BluetoothConnection.this.socket != null){
	            	Log.i("BluetoothConnection", "Got a socket");
	            	BluetoothConnection.this.socket.connect();
	            	Log.i("BluetoothConnection", "Socket setup");                
	            }        	
        	}
        	catch(Exception e){
        		this.errorMessage = e.getMessage();
        	}
        }
	}
	
	/*
	 * Opens the bluetooth connection with the specified port name
	 */
	public void openConnection(String port){
		synchronized(this.lock){
			String error_message = null;
	        try{
	        	BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
	        	adapter.cancelDiscovery();
	        	Set<BluetoothDevice> paired_devices = adapter.getBondedDevices();
	            for (BluetoothDevice device: paired_devices){
	            	String name = device.getName();
	                if (name.equals(port)){
	                	Log.i("BluetoothConnection", "trying " + name);
	                	
	                    ConnectThread ct = new ConnectThread(device);
	                    ct.start();
	                    ct.join(5000);
	                    error_message = ct.errorMessage;
	                    break;
	                }
	            }
	            if (this.socket != null){
		            this.recv_stream = this.socket.getInputStream();
		            this.send_stream = this.socket.getOutputStream();
		            this.reader = new BufferedReader(new InputStreamReader(this.recv_stream,"UTF-8"));
		            Log.i("BluetoothConnection", "Socket Ready");
	            }
	            else{
	                error_message = "Could not detect device " + port + ": " + String.valueOf(error_message);
	            }            
	        }
	        catch(Exception e){
	            error_message = "Error opening Bluetooth socket: " + e.getMessage();
	        }
	            
	        if (this.socket == null){
	            throw new RuntimeException("Error opening Bluetooth port: " + String.valueOf(error_message));
	        }
		}
	}
	
	/**
	 * Closes the current Bluetooth connection
	 */
	public void closeConnection(){
		synchronized(this.lock){		
			try{
	        	Log.i("BluetoothConnection", "Closing Socket");
	        	if (this.socket != null){
	                this.socket.close();        		
	        	}
	        }
	        catch (Throwable e){
	        }
	        finally{
	            this.socket = null;
	            this.recv_stream = null;
	            this.send_stream = null;
	            this.reader = null;
	        }
		}
	}
	
	/**
	 * Returns true if the connection is active
	 */
	public boolean isOpen(){
		return this.socket != null;
	}
	
	/**
	 * reads a line from the socket. If the socket is closed or no data is available, returns null
	 */
	public String readLine(){
		String line = null;
		synchronized(this.lock){
			try{
				if (this.reader != null){
					line =  this.reader.readLine();
				}
			}
			catch(Throwable e){}
		}
		return line;
	}
	
	/**
	 * Writes the specified data to the socket. Returns true if the write succeeded. 
	 */
	public boolean write(String data){
		synchronized(this.lock){
			try{
				if (this.send_stream != null){
					this.send_stream.write(data.getBytes());
					return true;
				}
				else{
					return false;
				}
			}
			catch(Throwable e){
				Log.i("BluetoothConnection", "Error writing data " + data + ": " + e.getMessage());
				this.closeConnection();
				return false;
			}
		}
	}

	public String[] getAvailableDevices(){
        BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        Set<BluetoothDevice> pairedDevices = bluetoothAdapter.getBondedDevices();

        List<String> devices = new ArrayList<String>();
        for(BluetoothDevice bt : pairedDevices)
            devices.add(bt.getName());

        return devices.toArray(new String[devices.size()]);
	}
}
