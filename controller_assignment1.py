from pox.core import core
import pox.lib.packet as pkt
import pox.lib.packet.ethernet as eth
import pox.lib.packet.arp as arp
import pox.lib.packet.icmp as icmp
import pox.lib.packet.ipv4 as ip
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr

log = core.getLogger()

table={}

rules=[{'eth-source': '00:00:00:00:00:01', 'eth-destination': '00:00:00:00:00:03', 'QoS': '0'}, 
       {'eth-source': '00:00:00:00:00:02', 'eth-destination': '00:00:00:00:00:03', 'QoS': '1'},
       {'eth-source': '00:00:00:00:00:01', 'eth-destination': '00:00:00:00:00:04', 'QoS': '0'},
       {'eth-source': '00:00:00:00:00:01', 'eth-destination': '00:00:00:00:00:02', 'QoS': 'block'},
       {'eth-source': '00:00:00:00:00:03', 'eth-destination': '00:00:00:00:00:04', 'QoS': 'block'}]

def launch ():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn",  _handle_PacketIn)
    log.info("Switch running.")

def _handle_ConnectionUp ( event):
    log.info("Starting Switch %s", dpidToStr(event.dpid))
    msg = of.ofp_flow_mod(command = of.OFPFC_DELETE)
    event.connection.send(msg)


def _handle_PacketIn ( event):
    dpid = event.connection.dpid
    sw=dpidToStr(event.dpid)
    inport = event.port
    packet = event.parsed
    log.debug("Event: switch %s port %s packet %s" % (sw, inport, packet))

    table[(event.connection, packet.src)] = event.port

    dst_port = table.get((event.connection, packet.dst))

    if dst_port is None: 
        install_rules(packet, event)

        msg = of.ofp_packet_out(data = event.ofp)
        msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
        event.connection.send(msg)
    else:
        # We must forward the incoming packet…
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port = dst_port))
        event.connection.send(msg)

        log.debug("Installing %s <-> %s" % (packet.src, packet.dst))

def install_rules(packet, event):
    for rule in rules:
        if rule['eth-source'] == packet.src and rule['eth-destination'] == packet.dst:
            if rule['QoS'] == 'block':
                block = of.ofp_match()
                block.dl_src = EthAddr(rule['eth-source'])
                block.dl_dst = EthAddr(rule['eth-destination'])
                msg = of.ofp_flow_mod()
                msg.match = block
                msg.priority = 32000
                msg.hard_timeout = 60
                event.connection.send(msg)
                return
            else: 
                limit = of.ofp_match()
                limit.dl_src = EthAddr(rule['eth-source'])
                limit.dl_dst = EthAddr(rule['eth-destination'])
                msg = of.ofp_flow_mod()
                msg.match = limit
                msg.priority = 32000
                msg.hard_timeout = 60

                if rule['eth-source'] == '00:00:00:00:00:01' and rule['eth-destination'] == '00:00:00:00:00:03':
                    msg.actions.append(of.ofp_action_output(port=3, queue_id=0))
                    event.connection.send(msg)
                    return
                elif rule['eth-source'] == '00:00:00:00:00:02' and rule['eth-destination'] == '00:00:00:00:00:03':
                    msg.actions.append(of.ofp_action_output(port=3, queue_id=1))
                    event.connection.send(msg)
                    return
                else:
                    msg.actions.append(of.ofp_action_output(port=4, queue_id=0))
                    event.connection.send(msg)
                    return

    msg = of.ofp_flow_mod()
    msg.priority=100
    msg.match.dl_dst = packet.src
    msg.match.dl_src = packet.dst
    msg.actions.append(of.ofp_action_output(port = event.port))
    event.connection.send(msg)
    return



        
        
        
    
    ######### Add new code hereThis is the part where you should loop over the rules you have defined    #########################################################
    ##############                                                                                                                                  ##############
    #### The most important part is that your controller installs a rule in the switch, according to the rules you have defined. It's important that if there  ###
    #### is a QoS requirement the flow rules makes use f teh appropriate queue - rhis queues are created in the other file                                     ###
    ###                                                                                                                                                        ###
    ### After this you should also forward the packet to the correct destination to avoid dropping it. All following packets will not come to the controller   ###
    ### if the rule is installed correctly                                                                                                                     ###
    ##############################################################################################################################################################
