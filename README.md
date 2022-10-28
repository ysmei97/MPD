# MPD

## Introduction

* Python 3 Implementation
* This is the demo for paper _MPD: Moving Target Defense through Communication Protocol Dialects_
* Implemented moving target defense using protocol dialects for FTP
* This prototype is designed for **get**, yet can be easily extend to other commands.


## Instructions

* Server end:
```shell
python server.py PORT_NUMBER
```

* Client end: 
```shell
python client.py SERVER_IP SERVER_PORT_NUMBER
```
  * Username and password are provided in _users.txt_

* **ServerFolder** and **ClientFolder** store server and clients files


## Citing MPD

If you use MPD in your research, please cite the [MPD paper](https://arxiv.org/abs/2110.03798).

*Mei, Y., Gogineni, K., Lan, T., & Venkataramani, G. (2021, September). MPD: Moving target defense through communication protocol dialects. In International Conference on Security and Privacy in Communication Systems (pp. 100-119). Springer, Cham.*

In BibTeX format:

```tex
@inproceedings{mei2021mpd,
  title={MPD: Moving target defense through communication protocol dialects},
  author={Mei, Yongsheng and Gogineni, Kailash and Lan, Tian and Venkataramani, Guru},
  booktitle={International Conference on Security and Privacy in Communication Systems},
  pages={100--119},
  year={2021},
  organization={Springer}
}
```

## More about DIALECT

[Communication Protocols Customization via Feature DIAgnosis, Lacing, Elimination, Cross-grafting, and Trimming](https://github.com/kailashg26/ONR_Dialect).




